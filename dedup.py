"""Find and merge duplicate companies in the 1P prospect database.

Usage:
    python3 dedup.py summary      show how many rows each input table has
"""
import argparse
import csv
from pathlib import Path

DATA_DIRECTORY = Path(__file__).parent / "data"

TABLE_NAMES = [
    "profiles",
    "prospects",
    "prospect_aliases",
    "prospect_contacts",
    "sdr_follow_up_tasks",
    "power_dialer_call_logs",
    "email_activities",
    "prospect_contact_notes",
    "prospect_meetings",
]


def load_tables(data_directory):
    """Read every input CSV into memory. Each row becomes a dict of column -> text."""
    tables = {}
    for table_name in TABLE_NAMES:
        csv_path = data_directory / f"{table_name}.csv"
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            tables[table_name] = list(csv.DictReader(csv_file))
    return tables


def print_summary(tables):
    for table_name, table_rows in tables.items():
        print(f"{table_name:<26} {len(table_rows):>3} rows")


def main():
    argument_parser = argparse.ArgumentParser(
        description="Find and merge duplicate companies in the 1P prospect database."
    )
    command_parsers = argument_parser.add_subparsers(dest="command", required=True)
    command_parsers.add_parser("summary", help="show how many rows each input table has")
    arguments = argument_parser.parse_args()

    tables = load_tables(DATA_DIRECTORY)
    if arguments.command == "summary":
        print_summary(tables)


if __name__ == "__main__":
    main()
