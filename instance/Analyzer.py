import nmap
import socket
import sys
import logging
from colorama import init, Fore, Style
init(autoreset=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scan_server(target, port_range="1-1024"):
    nm = nmap.PortScanner()
    results = {
        "target": target,
        "resolved_ip": None,
        "open_ports": [],
        "services": {},
        "potential_flaws": [],
        "os_info": "unknown",
        "error": None
    }

    try:
        # Resolve hostname to IP
        try:
            ip = socket.gethostbyname(target)
            results["resolved_ip"] = ip
            logging.info(f"Resolved {target} to {ip}")
        except socket.gaierror:
            results["error"] = f"Failed to resolve {target}."
            return results

        # Run Nmap scan
        scan_args = f"-sV -O -sC -p {port_range}"
        nm.scan(ip, arguments=scan_args)

        if ip not in nm.all_hosts():
            results["error"] = f"Host {ip} is unreachable."
            return results

        data = nm[ip]

        # OS detection
        if 'osmatch' in data and data['osmatch']:
            results["os_info"] = data['osmatch'][0].get('name', 'unknown')

        # Ports & services
        for proto in data.all_protocols():
            for port in sorted(data[proto].keys()):
                info = data[proto][port]
                if info['state'] == 'open':
                    results['open_ports'].append(port)
                    results['services'][port] = {
                        "service": info.get("name", "unknown"),
                        "product": info.get("product", "unknown"),
                        "version": info.get("version", "unknown"),
                        "extrainfo": info.get("extrainfo", "").strip(),
                        "state": info["state"]
                    }

                    # Heuristics
                    svc = info.get("name", "").lower()
                    prod = info.get("product", "")
                    ver = info.get("version", "")
                    if svc in ["ftp", "telnet"]:
                        results["potential_flaws"].append(f"Port {port}: Insecure service '{svc.upper()}' detected.")
                    if "Apache" in prod and ver and not ver.startswith("2.4."):
                        results["potential_flaws"].append(f"Port {port}: Possibly outdated Apache ({ver}).")
                    if "OpenSSH" in prod and ver and ver < "8.0":
                        results["potential_flaws"].append(f"Port {port}: Possibly outdated OpenSSH ({ver}).")

        # Host-wide vulnerability checks
        if "Windows XP" in results["os_info"] or "Windows Server 2008" in results["os_info"]:
            results["potential_flaws"].append(f"Outdated OS detected: {results['os_info']}")

        # Nmap script results
        if 'script' in data:
            for script_name, output in data['script'].items():
                if "vuln" in script_name or "exploit" in script_name:
                    results["potential_flaws"].append(f"Nmap script '{script_name}': {output.strip()}")

    except nmap.PortScannerError as e:
        results["error"] = f"Nmap error: {str(e)}"
    except Exception as e:
        results["error"] = f"Unhandled error: {str(e)}"

    return results

def print_results(results):
    print("\n" + Fore.CYAN + Style.BRIGHT + "="*60)
    if results["error"]:
        print(Fore.RED + Style.BRIGHT + f"ERROR: {results['error']}")
        print(Fore.CYAN + "="*60)
        return

    print(Fore.GREEN + Style.BRIGHT + f"SCAN REPORT FOR {results['target']} ({results['resolved_ip']})")
    print(Fore.CYAN + "="*60)

    print(Fore.MAGENTA + "\n--- Host & OS Info ---")
    print(f"Status: {Fore.GREEN if results['open_ports'] else Fore.RED}{'Up' if results['open_ports'] else 'Likely Down'}")
    print(f"OS: {Fore.YELLOW}{results['os_info']}")

    print(Fore.MAGENTA + "\n--- Open Ports ---")
    if results['open_ports']:
        for port in results['open_ports']:
            svc = results['services'][port]
            print(Fore.BLUE + f"  Port {port}: {svc['service']} ({svc['product']} {svc['version']})")
            if svc['extrainfo']:
                print(f"    Extra Info: {svc['extrainfo']}")
    else:
        print(Fore.YELLOW + "  No open ports found.")

    print(Fore.MAGENTA + "\n--- Potential Vulnerabilities ---")
    if results['potential_flaws']:
        for i, flaw in enumerate(sorted(set(results['potential_flaws'])), 1):
            print(Fore.RED + f"  {i}. {flaw}")
    else:
        print(Fore.GREEN + "  No major issues found.")

    print(Fore.CYAN + "="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python network_scanner.py <target> [port_range]")
        sys.exit(1)

    target = sys.argv[1]
    ports = sys.argv[2] if len(sys.argv) == 3 else "1-1024"
    result = scan_server(target, ports)
    print_results(result)
