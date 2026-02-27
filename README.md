# telnet_loader

Multi-threaded Telnet command loader. Connects to Telnet-enabled devices using pre-obtained credentials and executes commands across multiple hosts concurrently. Features shell detection, login validation, honeypot detection, retry logic, per-target timeouts, and incremental result output with a live status counter.

Tel0ader does not brute-force credentials or bypass authentication. Credential discovery must be handled separately.


---

## Requirements

`telnetlib` was removed in Python 3.13 (PEP 594). You need Python 3.12 or earlier.

No external dependencies. Everything is stdlib (`telnetlib`, `threading`, `argparse`, `re`, `time`, `socket`).

### pyenv (recommended)

```bash
pyenv install 3.11.9
pyenv local 3.11.9
python -c "import telnetlib; print('ok')"
```

### conda

```bash
conda create -n tel0ader python=3.11 -y
conda activate tel0ader
```

### venv (if 3.11 is already installed)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

---

## Target File Format

One target per line:

```
HOST:PORT USER:PASSWORD
```

Port defaults to `23` if omitted. Password can be empty (use `user:` with no value after the colon).

Example `targets.txt`:

```
18.181.177.7:23 root:root
221.1.120.79:23 admin:admin
192.168.1.1 admin:password
10.0.0.5:2323 user:
```

---

## Usage

```
python teloader.py -l <target_file> [options]
```

### Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-l, --list` | string | (required) | Path to target list file |
| `-t, --threads` | int | `10` | Number of concurrent threads |
| `-c, --command` | string | `uname -a` | Command to execute after login |
| `-o, --output` | string | (none) | Output file for results |
| `--timeout` | int | `10` | Per-operation timeout in seconds (connect, login prompt, password prompt, post-login) |
| `--max-time` | int | `4 * timeout` | Max total wall-clock seconds per target. Caps the entire login+execute cycle so a slow phase can't consume unbounded time |
| `--retries` | int | `0` | Number of retries for transient failures (timeout, refused, reset, EOF). Auth failures are never retried |

### Examples

Basic scan with 20 threads:

```bash
python teloader.py -l targets.txt -t 20
```

Custom command with output file:

```bash
python teloader.py -l targets.txt -t 10 -c "cat /proc/cpuinfo" -o results.txt
```

Aggressive timeout with retries:

```bash
python teloader.py -l targets.txt -t 50 --timeout 5 --max-time 15 --retries 2
```

Monitor results in real time from another terminal:

```bash
tail -f results.txt
```

---

## How It Works

1. Parses targets from the input file (host, port, user, password).
2. Opens the output file for incremental writing (if `-o` is specified).
3. Spawns a thread pool and connects to each target via Telnet.
4. For each target:
   - Connects with the configured timeout.
   - Waits for a login prompt, sends username.
   - Waits for a password prompt, sends password.
   - Checks for login failure messages (`Login incorrect`, `Access denied`, etc.) or a shell prompt.
   - Detects shell type and privilege level from the prompt pattern.
   - Runs honeypot detection against banner data and login timing.
   - Sends the command followed by `exit`.
   - Reads output using a deadline-bounded loop (never blocks indefinitely).
   - Writes the result to the output file immediately (thread-safe, flushed).
5. If the connection fails with a transient error and `--retries` > 0, retries with brief backoff (0.5s increments, max 2s).
6. Prints a colored summary to the console.

Every `expect()` call respects both `--timeout` (per-operation) and `--max-time` (per-target total), using whichever is smaller. This prevents any single slow phase from stalling the entire target.

---

## Shell Detection

After successful login, the prompt is matched against known patterns:

| Prompt Pattern | Label | Privilege |
|----------------|-------|-----------|
| `$ ` | sh | user |
| `# ` | root | root |
| `> ` | cli | user |
| `% ` | csh | user |
| `(hostname)#` | busybox | root |
| `(hostname)$` | busybox | user |

Post-login text is also scanned for keywords: `busybox`, `mikrotik`, `procd`, `/tc/` (OpenWrt). These override the prompt-based label when found.

---

## Honeypot Detection

Banner data and login timing are checked for common honeypot indicators:

- **Signature matching:** Scans for known honeypot software names in banner text (kippo, cowrie, dionaea, HonSSH, etc.).
- **Timing heuristic:** Flags logins that complete in under 50ms as suspicious, since real devices have measurable auth latency.

When a honeypot is detected, results are tagged with the reason (e.g., `HONEYPOT: honeypot signature: cowrie` or `HONEYPOT: suspiciously fast login response`). This appears in both console output and the output file.

---

## Output Format

### Console

Live counter pinned at the bottom of the terminal during execution:

```
  [Total: 100]  [Logins: 12]  [Commands: 12]  [Remaining: 88]
```

Results print above the counter as they arrive:

```
[+] SUCCESS: 10.0.0.1:23 (root) [busybox | root]
    Output: Linux device 4.14.81 armv7l GNU/Linux
[-] FAILED: 10.0.0.2:23 - Connection timed out
```

### File (`-o`)

Results are written incrementally as they complete, one line per target:

```
[+] 10.0.0.1:23 (root) [busybox | root]
    Linux device 4.14.81 armv7l GNU/Linux
[-] 10.0.0.2:23 - Connection timed out
```

A summary line is appended at the end:

```
Summary: 12 successful, 88 failed, 100 total
```

Because results are flushed immediately, the output file is crash-safe. Completed results are never lost even if the process is killed.

---

## Limitations

- ASCII command encoding only.
- No per-target command variation.
- No SOCKS/proxy support.
- `telnetlib` is deprecated since Python 3.11 (PEP 594) and removed in 3.13.

---

tel0ader v3 -- [@Syn2Much](https://github.com/Syn2Much)
