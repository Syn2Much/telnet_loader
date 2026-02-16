
# Tel0ader 📡

**Tel0ader** is a **multi-threaded Telnet command execution loader**  It connects to 
Telnet-enabled devices using **pre-obtained credentials** and executes a **user-supplied command or payload** across multiple hosts concurrently.
---

<img width="1458" height="758" alt="image" src="https://github.com/user-attachments/assets/f0480a54-c53c-4b3a-982f-2d640aa96f1d" />

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



## 🔒 Security & Legal Notice

**This tool is for authorized testing only.**

The author assumes **no liability** for misuse.

---
## ⚠️ Limitations

Assumes standard Telnet login prompts

* ASCII command encoding only
* No retry logic
* No per-target command variation
* These are intentional design choices to keep the tool simple and auditable.

---
## 📜 Version

**tel0ader v2**
Developed by **@Syn2Much**

---

