
# Tel0ader 📡

**Tel0ader** is a **multi-threaded Telnet command execution loader** designed for **mirai style combo list**.

It connects to Telnet-enabled devices using **pre-obtained credentials** and executes a **user-supplied command or payload** across multiple hosts concurrently.

> ⚠️ Tel0ader **does not brute-force credentials**, **does not bypass authentication**, and **does not perform honeypot detection**. Credential discovery must be handled separately.

---


## ✨ Features

* ⚡ **Multi-threaded execution**
* 🔐 **Credential-based Telnet login**
* 🧾 **Command output capture**
* 📄 **Optional result logging to file**
* ⏱️ **Configurable connection timeout**
* 🧵 **Thread-safe console output**
* 🧪 **Lightweight & dependency-free**

---

## 📦 Requirements

* Python **3.8+**
* Valid Telnet credentials
* Explicit authorization to test targets

---

## 📂 Target List Format

Targets must be provided via a file, **one per line**, using the following format:

```
IP:PORT USER:PASSWORD
```

### Example

```txt
18.181.177.7:23 root:root
221.1.120.79:23 admin:admin
```

## 🚀 Usage

```bash
python loader.py -l targets.txt -t 20 -c "uname -a" -o results.txt
```

### Arguments

| Flag            | Description                                          |
| --------------- | ---------------------------------------------------- |
| `-l, --list`    | File containing target list (**required**)           |
| `-t, --threads` | Number of concurrent threads (default: 10)           |
| `-c, --command` | Command to execute after login (default: `uname -a`) |
| `-o, --output`  | File to save results                                 |
| `--timeout`     | Connection timeout in seconds (default: 10)          |

---

## 🧠 How It Works

1. Loads targets from file
2. Parses `host`, `port`, `username`, and `password`
3. Creates a thread pool
4. For each target:

   * Connects via Telnet
   * Handles common login prompts
   * Authenticates with provided credentials
   * Executes the supplied command
   * Captures output
   * Disconnects cleanly
5. Aggregates results and prints a summary
6. Optionally writes results to disk

---


## 📄 Output Behavior

### Console Output

* Successful connections are marked with `[+]`
* Failures are marked with `[-]`
* Errors include timeout, refusal, or disconnect reasons

### Output File (`-o`)

If specified, results are saved in two sections:

* **Successful Connections**

  * Host
  * Username
  * Command output
* **Failed Connections**

  * Host
  * Error reason

---


## 🔒 Security & Legal Notice

**This tool is for authorized testing only.**

Unauthorized access, command execution, or abuse of Telnet services may violate:

* Computer misuse laws
* Network abuse policies
* Terms of service

The author assumes **no liability** for misuse.

---


## 📜 Version

**tel0ader v1**
Developed by **@Syn2Much**

---

