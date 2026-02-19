# Tel0ader

A multi-threaded Telnet command execution loader that connects to Telnet-enabled devices using pre-obtained credentials and executes a user-supplied command across multiple hosts concurrently — with shell detection, login validation, and a live status counter.

> Tel0ader does **not** brute-force credentials, bypass authentication, or perform honeypot detection. Credential discovery must be handled separately.

**This tool is for authorized testing only.** The author assumes no liability for misuse.

---

## Setup

`telnetlib` was removed in Python 3.13 (deprecated since 3.11 via PEP 594). You need a Python environment that still includes it.

### Using pyenv (recommended)

```bash
# Install pyenv if you don't have it
curl https://pyenv.run | bash

# Install Python 3.11 and create a local env
pyenv install 3.11.9
pyenv local 3.11.9

# Verify
python --version   # Python 3.11.9
python -c "import telnetlib; print('telnetlib available')"
```

### Using conda

```bash
conda create -n tel0ader python=3.11 -y
conda activate tel0ader
```

### Using venv (if 3.11 is already installed)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

No additional dependencies — `telnetlib`, `threading`, and `argparse` are all stdlib.

---

## Target List Format

Targets are provided via a file, one per line:

```
IP:PORT USER:PASSWORD
```

Port defaults to `23` if omitted. Password can be empty.

```
18.181.177.7:23 root:root
221.1.120.79:23 admin:admin
192.168.1.1 admin:password
```

---

## Usage

```bash
python teloader.py -l targets.txt -t 20 -c "uname -a" -o results.txt
```

| Flag            | Description                                          |
| --------------- | ---------------------------------------------------- |
| `-l, --list`    | File containing target list (required)               |
| `-t, --threads` | Number of concurrent threads (default: `10`)         |
| `-c, --command` | Command to execute after login (default: `uname -a`) |
| `-o, --output`  | File to save results                                 |
| `--timeout`     | Connection timeout in seconds (default: `10`)        |

---

## How It Works

1. Parses targets from the input file (host, port, user, password).
2. Spawns a thread pool and connects to each target via Telnet.
3. For each target: waits for a login prompt, sends credentials, validates authentication (fails fast on rejection messages like `Login incorrect` or `Access denied`), detects shell type and privilege level, executes the supplied command, captures output, and disconnects.
4. Prints a colored summary and optionally writes detailed results to disk.

---

## Shell Detection

After successful auth, the prompt pattern is matched to identify the shell environment:

| Prompt Pattern     | Label      | Privilege |
| ------------------ | ---------- | --------- |
| `$ `               | `sh`       | user      |
| `# `               | `root`     | root      |
| `> `               | `cli`      | user      |
| `% `               | `csh`      | user      |
| `(hostname)#`      | `busybox`  | root      |
| `(hostname)$`      | `busybox`  | user      |

Secondary heuristics refine detection by scanning post-login text for keywords like `busybox`, `mikrotik`, `procd`, or `/tc/` (OpenWrt).

---

## Output

**Console:** `[+]` for successful connections (with shell tag like `[sh | root]`), `[-]` for failures with reason.

**File (`-o`):** Results split into successful and failed sections. Successful entries include host, user, detected shell/privilege, and command output.

**Live counter** stays pinned at the bottom of the terminal during execution showing total, logins, commands executed, and remaining targets.

---

## Limitations

- ASCII command encoding only
- No retry logic
- No per-target command variation
- `telnetlib` is deprecated since Python 3.11 (PEP 594) — see [Setup](#setup)
- These are intentional design choices to keep the tool simple and auditable.

---

tel0ader v2 — [@Syn2Much](https://github.com/Syn2Much)
