"""Find and merge duplicate companies in the 1P prospect database.

Usage:
    python3 dedup.py summary      show how many rows each input table has
"""
import argparse
import csv
from pathlib import Path
from urllib.parse import urlsplit

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

# Domains anyone can have an address on. They never identify a company.
GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com",
}


def load_tables(data_directory):
    """Read every input CSV into memory. Each row becomes a dict of column -> text."""
    tables = {}
    for table_name in TABLE_NAMES:
        csv_path = data_directory / f"{table_name}.csv"
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            tables[table_name] = list(csv.DictReader(csv_file))
    return tables


def website_identity_key(website):
    """Turn a website as imported into the key that identifies the company.

    Returns None when the website cannot identify a company.
    """
    website_text = website.strip()
    if "://" not in website_text:
        website_text = "//" + website_text      # urlsplit only finds the host after "//"
    host_name = urlsplit(website_text).hostname or ""
    host_labels = host_name.split(".")           # "waco.zenithstamping.com" -> 3 labels
    host_looks_like_a_domain = len(host_labels) >= 2
    if not host_looks_like_a_domain:
        return None
    root_domain = ".".join(host_labels[-2:])     # keep the last two: "zenithstamping.com"
    if root_domain in GENERIC_DOMAINS:
        return None
    return root_domain


def phone_identity_key(phone):
    """Turn a phone as imported into its ten digits, or None if it is not a full US number."""
    phone_digits = "".join(character for character in phone if character.isdigit())
    has_us_country_code = len(phone_digits) == 11 and phone_digits.startswith("1")
    if has_us_country_code:
        phone_digits = phone_digits[1:]
    if len(phone_digits) != 10:
        return None
    return phone_digits


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
