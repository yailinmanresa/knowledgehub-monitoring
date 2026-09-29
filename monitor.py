"""Knowledge Hub monitoring tool.

Measures system metrics (CPU, memory, disk) and stores them in a
SQLite database, or reports stored measurements over a time period.

Examples:
    python monitor.py measure
    python monitor.py measure --metrics cpu-usage memory-usage
    python monitor.py measure --reset
    python monitor.py report --start 2026-09-29
    python monitor.py report --start "2026-09-29 10:00" --end now
"""

import argparse
import logging
import sqlite3
import sys
from datetime import datetime

import psutil

DB_FILE = "measurements.db"
LOG_FILE = "monitor.log"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def measure_cpu():
    """Return the CPU usage in percent, measured over one second."""
    return psutil.cpu_percent(interval=1)


def measure_memory():
    """Return the memory (RAM) usage in percent."""
    return psutil.virtual_memory().percent


def measure_disk():
    """Return the usage of the main disk in percent."""
    return psutil.disk_usage("/").percent


# Every metric the tool recognizes, with the function that measures it.
METRICS = {
    "cpu-usage": measure_cpu,
    "memory-usage": measure_memory,
    "disk-usage": measure_disk,
}


def connect_db(path):
    """Open the database and create the table if it does not exist yet."""
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS measurements ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " timestamp TEXT NOT NULL,"
        " metric TEXT NOT NULL,"
        " value REAL NOT NULL)"
    )
    return connection


def reset_db(connection):
    """Delete all stored measurements (only used with --reset)."""
    connection.execute("DELETE FROM measurements")
    connection.commit()
    logging.warning("All stored measurements were deleted (--reset)")
    print("All stored measurements were deleted.")


def measure(connection, metric_names):
    """Measure the given metrics and add them to the database."""
    timestamp = datetime.now().strftime(TIME_FORMAT)
    for name in metric_names:
        value = METRICS[name]()
        connection.execute(
            "INSERT INTO measurements (timestamp, metric, value)"
            " VALUES (?, ?, ?)",
            (timestamp, name, value),
        )
        logging.info("Measured %s = %.1f%%", name, value)
        print(f"{timestamp}  {name:<14}{value:>7.1f}%")
    connection.commit()


def parse_time(text, end_of_day=False):
    """Turn a date or date/time text into the format used in the database.

    A date without a time counts as the start of that day, or as the end
    of that day when end_of_day is True. The word "now" means the
    current time.
    """
    if text == "now":
        return datetime.now().strftime(TIME_FORMAT)
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"'{text}' is not a valid date or time, "
            "use for example 2026-09-29 or '2026-09-29 14:00'"
        ) from None
    if end_of_day and len(text) == 10:
        moment = moment.replace(hour=23, minute=59, second=59)
    return moment.strftime(TIME_FORMAT)


def report(connection, start, end, metric=None):
    """Show stored measurements between start and end, with averages."""
    query = (
        "SELECT timestamp, metric, value FROM measurements"
        " WHERE timestamp BETWEEN ? AND ?"
    )
    parameters = [start, end]
    if metric:
        query += " AND metric = ?"
        parameters.append(metric)
    query += " ORDER BY timestamp, metric"
    rows = connection.execute(query, parameters).fetchall()

    print(f"\nMeasurements from {start} to {end}")
    print("=" * 45)
    if not rows:
        print("No measurements found in this period.")
        return

    print(f"{'Timestamp':<21}{'Metric':<16}{'Value':>8}")
    print("-" * 45)
    values_per_metric = {}
    for timestamp, name, value in rows:
        print(f"{timestamp:<21}{name:<16}{value:>7.1f}%")
        values_per_metric.setdefault(name, []).append(value)

    print("-" * 45)
    for name, values in values_per_metric.items():
        average = sum(values) / len(values)
        print(
            f"{'Average ' + name:<37}{average:>7.1f}%"
            f"  ({len(values)}x)"
        )
    logging.info("Report %s to %s: %d measurements", start, end, len(rows))


def build_parser():
    """Define the command-line options of the tool."""
    parser = argparse.ArgumentParser(
        description="Knowledge Hub monitoring tool: measure system "
        "metrics or report stored measurements.",
    )
    parser.add_argument(
        "--db",
        default=DB_FILE,
        help="SQLite database file (default: %(default)s)",
    )
    modes = parser.add_subparsers(dest="mode", required=True)

    measure_parser = modes.add_parser(
        "measure", help="measure metrics and store them"
    )
    measure_parser.add_argument(
        "--metrics",
        nargs="+",
        choices=list(METRICS),
        default=list(METRICS),
        help="metrics to measure (default: all)",
    )
    measure_parser.add_argument(
        "--reset",
        action="store_true",
        help="delete all stored measurements before measuring",
    )

    report_parser = modes.add_parser(
        "report", help="show stored measurements for a time period"
    )
    report_parser.add_argument(
        "--start",
        required=True,
        help="start date or time, e.g. 2026-09-29 or '2026-09-29 14:00'",
    )
    report_parser.add_argument(
        "--end",
        default="now",
        help="end date or time (default: now)",
    )
    report_parser.add_argument(
        "--metric",
        choices=list(METRICS),
        help="only show this metric",
    )
    return parser


def main():
    """Read the command-line options and run the chosen mode."""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = build_parser().parse_args()
    connection = connect_db(args.db)
    try:
        if args.mode == "measure":
            if args.reset:
                reset_db(connection)
            measure(connection, args.metrics)
        else:
            start = parse_time(args.start)
            end = parse_time(args.end, end_of_day=True)
            report(connection, start, end, args.metric)
    except ValueError as error:
        logging.error(error)
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
