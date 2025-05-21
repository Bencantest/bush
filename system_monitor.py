# system_monitor.py
import psutil
import argparse
import time
import sys
import os

# Import the aimonitor script

try:
    import aimon
except ImportError:
    print("Error: Could not import aimonitor.py.")
    print("Please ensure aimonitor.py is in the same directory as system_monitor.py")
    sys.exit(1)


def get_system_info():
    """
    Gathering basic system information.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()

        system_info = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_info.percent,
            "disk_percent": disk_usage.percent,
            "bytes_sent": net_io.bytes_sent,
            "bytes_received": net_io.bytes_recv,
        }
        return system_info
    except Exception as e:
        print(f"Error gathering system info: {e}")
        return {}


def list_processes(procname=None, cmdline=None):
    """
    Lists processes with optional filtering by name or command line.
    -Return a list of process dictionaries.
    """
    processes = []
    # Specify attributes we are interested in to potentially speed up
    attrs = ['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'memory_info']
    for p in psutil.process_iter(attrs):
        try:
            pinfo = p.info
            if procname and procname.lower() not in pinfo.get('name', '').lower():
                continue
            # Ensure cmdline is not None before joining and searching
            process_cmdline = " ".join(pinfo.get('cmdline', []) or [])
            if cmdline and cmdline.lower() not in process_cmdline.lower():
                continue

            processes.append({
                "pid": pinfo.get('pid'),
                "name": pinfo.get('name'),
                "username": pinfo.get('username'),
                "cmdline": process_cmdline,
                "cpu_percent": pinfo.get('cpu_percent'),
                "memory_percent": getattr(pinfo.get('memory_info'), 'percent', None),
                "rss": getattr(pinfo.get('memory_info'), 'rss', 0)  # Add RSS for memory-based checks
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            # Ignore processes that vanish or deny access during iteration
            continue
        except Exception as e:
            print(f"Error processing process {pinfo.get('pid', 'N/A')}: {e}")
            continue

    return processes


def get_top_cpu_processes(limit=3):
    """
    Returns a list of processes consuming the most CPU time.
    :param limit: The number of top processes to return.
    """
    processes_with_cpu_times = []
    # Need to fetch cpu_times for sorting
    for p in psutil.process_iter(['pid', 'name', 'cpu_times', 'username']):
        try:
            pinfo = p.info
            cpu_times = pinfo.get('cpu_times')
            if cpu_times:
                total_cpu_time = sum(cpu_times[:2])  # Sum user and system time
                processes_with_cpu_times.append({
                    "pid": pinfo.get('pid'),
                    "name": pinfo.get('name'),
                    "username": pinfo.get('username'),
                    "total_cpu_time": total_cpu_time
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue
        except Exception as e:
            print(f"Error getting CPU times for process {pinfo.get('pid', 'N/A')}: {e}")
            continue

    # Sort by total_cpu_time in descending order
    sorted_processes = sorted(processes_with_cpu_times, key=lambda x: x.get('total_cpu_time', 0), reverse=True)
    return sorted_processes[:limit]


def get_memory_range_processes(min_mb, max_mb):
    """
    Returns a list of processes consuming memory within the specified range (in MB).
    :param min_mb: Minimum memory usage in MB.
    :param max_mb: Maximum memory usage in MB.
    """
    min_bytes = min_mb * 1024 * 1024
    max_bytes = max_mb * 1024 * 1024

    matching_processes = []
    # Need to fetch memory_info for RSS
    for p in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
        try:
            pinfo = p.info
            mem_info = pinfo.get('memory_info')
            if mem_info and mem_info.rss:
                rss_bytes = mem_info.rss
                if min_bytes <= rss_bytes <= max_bytes:
                    matching_processes.append({
                        "pid": pinfo.get('pid'),
                        "name": pinfo.get('name'),
                        "username": pinfo.get('username'),
                        "rss_mb": rss_bytes / (1024 * 1024)
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue
        except Exception as e:
            print(f"Error getting memory info for process {pinfo.get('pid', 'N/A')}: {e}")
            continue

    # Sort by memory usage (descending) for better readability
    return sorted(matching_processes, key=lambda x: x.get('rss_mb', 0), reverse=True)


def run_background_monitor(interval=60, ai_check_interval=300):
    """
    Run the system monitor in the background, periodically sending data to AI.
     interval: Interval in seconds to collect system data.
     ai_check_interval: Interval in seconds to send data to AI for analysis.
    """
    print("Running system monitor in background...")
    last_ai_check_time = time.time()

    # Initialize AI client once
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print("Error: GROQ_API_KEY environment variable not set for AI analysis.")
        print("AI analysis will be skipped.")
        ai_client = None
    else:
        try:
            ai_client = aimon.initialize_client(groq_api_key)
            print("AI client initialized successfully.")
        except Exception as e:
            print(f"Error initializing AI client: {e}")
            print("AI analysis will be skipped.")
            ai_client = None

    try:
        while True:
            current_time = time.time()

            # Collect data
            system_info = get_system_info()
            processes = list_processes()  # Get all processes for AI analysis

            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Collected system data. CPU: {system_info.get('cpu_percent', 'N/A')}%")

            # Send data to AI periodically
            if ai_client and (current_time - last_ai_check_time) >= ai_check_interval:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sending data to AI...")
                # Pass collected data to the AI monitor function
                aimon.analyze_system_data(ai_client, system_info, processes)
                last_ai_check_time = current_time

            # Wait for the next interval
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nBackground monitoring stopped by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during background monitoring: {e}")


def main():
    parser = argparse.ArgumentParser(description="Monitor system activity and list processes.")
    parser.add_argument('--system', action='store_true', help='Show overall system information.')
    parser.add_argument('--processes', action='store_true', help='List running processes.')
    parser.add_argument('-n', '--procname', type=str, help='Filter processes by name.')
    parser.add_argument('-c', '--cmdline', type=str, help='Filter processes by command line.')
    parser.add_argument('--run-in-background', action='store_true',
                        help='Run the monitor in the background and send data to AI periodically.')
    parser.add_argument('--interval', type=int, default=10,
                        help='Interval in seconds for collecting system data in background mode.')
    parser.add_argument('--ai-interval', type=int, default=10,
                        help='Interval in seconds for sending data to AI for analysis in background mode.')

    # arguments for specific process checks
    parser.add_argument('--top-cpu', type=int, metavar='N', help='Show top N processes consuming most CPU time.')
    parser.add_argument('--mem-range', type=float, nargs=2, metavar=('MIN_MB', 'MAX_MB'),
                        help='Show processes consuming memory between MIN_MB and MAX_MB.')

    args = parser.parse_args()

    if args.run_in_background:
        run_background_monitor(interval=args.interval, ai_check_interval=args.ai_interval)
        return

    # Existing command line functionalities
    if args.system:
        system_info = get_system_info()
        print("--- System Information ---")
        print(f"CPU Usage: {system_info.get('cpu_percent', 'N/A')}%")
        print(f"Memory Usage: {system_info.get('memory_percent', 'N/A')}%")
        print(f"Disk Usage: {system_info.get('disk_percent', 'N/A')}%")
        print(f"Network Sent (bytes): {system_info.get('bytes_sent', 'N/A')}")
        print(f"Network Received (bytes): {system_info.get('bytes_received', 'N/A')}")

    elif args.processes:  # Use elif to ensure only one main action is performed
        processes = list_processes(args.procname, args.cmdline)
        print("\n--- Running Processes ---")
        if processes:
            for p in processes:
                mem_percent_display = f"{p.get('memory_percent', 'N/A'):.2f}%" if isinstance(p.get('memory_percent'),
                                                                                             float) else "N/A"
                print(
                    f"PID: {p.get('pid', 'N/A')}, Name: {p.get('name', 'N/A')}, User: {p.get('username', 'N/A')}, CPU: {p.get('cpu_percent', 'N/A')}%, Memory: {mem_percent_display}")
                if p.get('cmdline'):
                    print(f"  Cmdline: {p.get('cmdline')}")
        else:
            print("No processes found matching criteria.")

    # New CL functionalities
    elif args.top_cpu is not None:
        top_cpu_processes = get_top_cpu_processes(args.top_cpu)
        print(f"\n--- Top {args.top_cpu} Processes by CPU Time ---")
        if top_cpu_processes:
            for p in top_cpu_processes:
                print(
                    f"PID: {p.get('pid', 'N/A')}, Name: {p.get('name', 'N/A')}, User: {p.get('username', 'N/A')}, Total CPU Time: {p.get('total_cpu_time', 'N/A'):.2f}s")
        else:
            print("No processes found or unable to retrieve CPU times.")

    elif args.mem_range is not None:
        min_mb, max_mb = args.mem_range
        mem_range_processes = get_memory_range_processes(min_mb, max_mb)
        print(f"\n--- Processes Consuming {min_mb:.2f}MB to {max_mb:.2f}MB Memory (RSS) ---")
        if mem_range_processes:
            for p in mem_range_processes:
                print(
                    f"PID: {p.get('pid', 'N/A')}, Name: {p.get('name', 'N/A')}, User: {p.get('username', 'N/A')}, Memory (RSS): {p.get('rss_mb', 'N/A'):.2f}MB")
        else:
            print(f"No processes found consuming memory between {min_mb:.2f}MB and {max_mb:.2f}MB.")

    if not any([args.system, args.processes, args.run_in_background, args.top_cpu, args.mem_range]):
        parser.print_help()

if __name__ == "__main__":
    main()