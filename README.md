# Tel0ader

**This is a multithreaded telnet loader it connects to each telnet device in your combo list and executes the user provided command/payload. It does not crack passwords or do honeypot checks the tool you use to get the combos should handle that.**

I reccomended bruteforcer https://github.com/CirqueiraDev/botnet-exploits/blob/main/bruteforce/brute.py


# Example usage:
  
  **python loader.py -l targets.txt -t 20 -c "whoami**
  
  **python loader.py -l targets.txt -t 5 -o results.txt**
---

Target file format (one per line):
  IP:PORT USER:PASSWORD
  
  18.181.177.7:23 root:root
  
  221.1.120.79:23 admin:admin
  
