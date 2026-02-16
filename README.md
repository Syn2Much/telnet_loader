
# Tel0ader 📡

> A **multi-threaded Telnet command execution loader** that connects to Telnet-enabled devices using **pre-obtained credentials** and executes a **user-supplied command** across multiple hosts concurrently — with **shell detection**, **login validation**, and a **live status counter**.

> ⚠️ Tel0ader **does not brute-force credentials**, **does not bypass authentication**, and **does not perform honeypot detection**. Credential discovery must be handled separately.

---

<img width="1458" height="758" alt="image" src="https://github.com/user-attachments/assets/f0480a54-c53c-4b3a-982f-2d640aa96f1d" />

## 📦 Requirements

* Python **3.8+**
* No external dependencies (stdlib only)
* Valid Telnet credentials
* Explicit authorization to test targets

---

## 📂 Target List Format

Targets are provided via a file, **one per line**:

```
IP:PORT USER:PASSWORD
```

Port defaults to `23` if omitted. Password can be empty.

```txt
18.181.177.7:23 root:root
221.1.120.79:23 admin:admin
192.168.1.1 admin:password
```

---

## 🚀 Usage

```bash
python teloader.py -l targets.txt -t 20 -c "uname -a" -o results.txt
```

### Arguments

| Flag            | Description                                          |
| --------------- | ---------------------------------------------------- |
| `-l, --list`    | File containing target list (**required**)           |
| `-t, --threads` | Number of concurrent threads (default: `10`)         |
| `-c, --command` | Command to execute after login (default: `uname -a`) |
| `-o, --output`  | File to save results                                 |
| `--timeout`     | Connection timeout in seconds (default: `10`)        |

---

## 🧠 How It Works

1. Loads and parses targets from file (`host`, `port`, `user`, `password`)
2. Spawns a thread pool and connects to each target via Telnet
3. For each target:
   * Waits for a login prompt (`login:`, `Login:`, `Username:`, `username:`)
   * Sends credentials and waits for a password prompt
   * **Validates login** — detects rejection messages (`Login incorrect`, `Access denied`, `Authentication failed`, etc.) and fails fast instead of hanging
   * **Detects shell type** — identifies the prompt style and reports both the shell family and privilege level
   * Executes the supplied command and captures output
   * Disconnects cleanly
4. Aggregates results and prints a colored summary
5. Optionally writes detailed results to disk

---

## 🐚 Shell Detection

After successful authentication, Tel0ader identifies the shell environment by matching the prompt pattern:

| Prompt Pattern     | Label      | Privilege |
| ------------------ | ---------- | --------- |
| `$ `               | `sh`       | user      |
| `# `               | `root`     | root      |
| `> `               | `cli`      | user      |
| `% `               | `csh`      | user      |
| `(hostname)#`      | `busybox`  | root      |
| `(hostname)$`      | `busybox`  | user      |

**Secondary heuristics** refine detection further by scanning post-login text:

| Keyword in banner | Detected as  |
| ----------------- | ------------ |
| `busybox`         | `busybox`    |
| `mikrotik`        | `mikrotik`   |
| `procd` or `/tc/` | `openwrt`    |

Shell type and privilege level are shown inline in console output and written to the results file.

---

## 📊 Live Status Counter

A real-time colored counter bar stays pinned at the bottom of the terminal during execution:

```
  [Total: 50]  [Logins: 12]  [Commands: 12]  [Remaining: 38]
```

| Counter      | Color  | Meaning                          |
| ------------ | ------ | -------------------------------- |
| **Total**    | White  | Total targets loaded             |
| **Logins**   | Green  | Successful authentications       |
| **Commands** | Yellow | Commands successfully executed   |
| **Remaining**| Cyan   | Targets not yet processed        |

The counter updates after every connection attempt and clears before the final summary.

---

## 📄 Output

### Console

* `[+]` — Successful connection (green), with detected shell tag: `[sh | root]`
* `[-]` — Failed connection (red), with reason: timeout, refused, login rejected, no prompt, etc.

### File (`-o`)

Results are split into **SUCCESSFUL CONNECTIONS** and **FAILED CONNECTIONS** sections. Successful entries include host, user, detected shell/privilege, and command output.

---

## 🔒 Security & Legal Notice

**This tool is for authorized testing only.**

The author assumes **no liability** for misuse.

---

## ⚠️ Limitations

* ASCII command encoding only
* No retry logic
* No per-target command variation
* `telnetlib` is deprecated since Python 3.11 (PEP 594)
* These are intentional design choices to keep the tool simple and auditable.

---

## 📜 Version

**tel0ader v2**
Developed by **@Syn2Much**
