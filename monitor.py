"""Initial system monitoring configuration tool.

Week 1 version: collects information about a system to be monitored
(hostname, IP address, and a list of metrics to track) and displays it
in a well-formatted summary. All data is stored in memory only; no
persistent storage or actual metric collection is implemented yet.
"""


def get_system_info():
    """Prompt the user for the target system's hostname and IP address.

    Returns:
        dict: A dictionary with keys 'hostname' and 'ip_address'.
    """
    hostname = input("Enter the hostname of the system to monitor: ").strip()
    ip_address = input("Enter the IP address of the system: ").strip()
    return {"hostname": hostname, "ip_address": ip_address}


def get_metrics():
    """Prompt the user to enter one or more metric names to track.

    The user enters metric names one at a time and presses Enter on an
    empty line to finish. Metric names can be anything the user
    chooses (e.g. cpu-usage, disk-0-usage, memory-usage).

    Returns:
        list[str]: A list of metric names entered by the user.
    """
    metrics = []
    print("\nEnter the metrics you want to monitor.")
    print("Press Enter on an empty line when you are done.\n")

    while True:
        prompt = f"Metric {len(metrics) + 1} (Enter to finish): "
        metric = input(prompt).strip()

        if not metric:
            if metrics:
                break
            print("You must enter at least one metric.")
            continue

        metrics.append(metric)

    return metrics


def display_summary(system_info, metrics):
    """Display the collected system information and metrics.

    Args:
        system_info (dict): Dictionary with 'hostname' and 'ip_address'.
        metrics (list[str]): List of metric names to monitor.
    """
    width = 50

    print("\n" + "=" * width)
    print("MONITORING CONFIGURATION SUMMARY".center(width))
    print("=" * width)

    print(f"{'Hostname:':<15}{system_info['hostname']}")
    print(f"{'IP address:':<15}{system_info['ip_address']}")

    print("-" * width)
    print("Metrics to monitor:")

    for index, metric in enumerate(metrics, start=1):
        print(f"  {index}. {metric}")

    print("=" * width + "\n")


def main():
    """Run the monitoring configuration tool."""
    print("System Monitoring Setup - Week 1")
    print("This tool collects information about a system to monitor.\n")

    system_info = get_system_info()
    metrics = get_metrics()
    display_summary(system_info, metrics)


if __name__ == "__main__":
    main()
