"""Find and merge duplicate companies in the 1P prospect database.

Usage:
    python3 dedup.py summary      show how many rows each input table has
    python3 dedup.py keys         show the identity keys of every company
    python3 dedup.py groups       show the duplicate groups and why each row is in them
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


def find_duplicate_groups(prospects):
    """Group the companies that share an identity.

    Returns (duplicate_groups, review_items). A duplicate group has two or more companies.
    """
    prospects_by_identity_key = {}
    match_reason_by_prospect_code = {}
    prospects_without_website_key = []

    # First: companies with a usable website are grouped by root domain.
    for prospect in prospects:
        website_key = website_identity_key(prospect["website"])
        if website_key is None:
            prospects_without_website_key.append(prospect)
            continue
        prospects_by_identity_key.setdefault(website_key, []).append(prospect)
        match_reason_by_prospect_code[prospect["prospect_code"]] = f"website domain {website_key}"

    # Index: main phone -> website domains that use it.
    website_keys_by_phone_key = {}
    for website_key, prospects_with_website in prospects_by_identity_key.items():
        for prospect in prospects_with_website:
            phone_key = phone_identity_key(prospect["phone"])
            if phone_key is not None:
                website_keys_by_phone_key.setdefault(phone_key, set()).add(website_key)

    # Then: companies without a usable website are identified by main phone.
    review_items = []
    for prospect in prospects_without_website_key:
        phone_key = phone_identity_key(prospect["phone"])
        if phone_key is None:
            review_items.append({
                "prospect_code": prospect["prospect_code"],
                "reason": "no website and no main phone: cannot tell if it is a duplicate",
            })
            continue
        website_keys_with_this_phone = sorted(website_keys_by_phone_key.get(phone_key, []))
        if len(website_keys_with_this_phone) > 1:
            review_items.append({
                "prospect_code": prospect["prospect_code"],
                "reason": f"no website; main phone {phone_key} is used by several companies: "
                          + ", ".join(website_keys_with_this_phone),
            })
            continue
        if len(website_keys_with_this_phone) == 1:
            identity_key = website_keys_with_this_phone[0]
            match_reason = f"no website; main phone {phone_key} belongs to {identity_key}"
        else:
            identity_key = f"phone {phone_key}"
            match_reason = f"no website; main phone {phone_key}"
        prospects_by_identity_key.setdefault(identity_key, []).append(prospect)
        match_reason_by_prospect_code[prospect["prospect_code"]] = match_reason

    duplicate_groups = [
        {
            "identity_key": identity_key,
            "prospects": prospects_in_group,
            "match_reasons": {
                prospect["prospect_code"]: match_reason_by_prospect_code[prospect["prospect_code"]]
                for prospect in prospects_in_group
            },
        }
        for identity_key, prospects_in_group in prospects_by_identity_key.items()
        if len(prospects_in_group) >= 2
    ]
    return duplicate_groups, review_items


def print_summary(tables):
    for table_name, table_rows in tables.items():
        print(f"{table_name:<26} {len(table_rows):>3} rows")


def print_identity_keys(prospects):
    print(f"{'code':<9} {'shop name':<31} {'website key':<22} phone key")
    for prospect in prospects:
        website_key = website_identity_key(prospect["website"]) or "-"
        phone_key = phone_identity_key(prospect["phone"]) or "-"
        print(f"{prospect['prospect_code']:<9} {prospect['shop_name']:<31} {website_key:<22} {phone_key}")


def print_duplicate_groups(duplicate_groups, review_items):
    print(f"DUPLICATE GROUPS ({len(duplicate_groups)})")
    for duplicate_group in duplicate_groups:
        print(f"\n{duplicate_group['identity_key']}")
        for prospect in duplicate_group["prospects"]:
            match_reason = duplicate_group["match_reasons"][prospect["prospect_code"]]
            print(f"  {prospect['prospect_code']}  {prospect['shop_name']:<31} {match_reason}")
    print(f"\nNEEDS REVIEW ({len(review_items)})")
    for review_item in review_items:
        print(f"  {review_item['prospect_code']}  {review_item['reason']}")


def main():
    argument_parser = argparse.ArgumentParser(
        description="Find and merge duplicate companies in the 1P prospect database."
    )
    command_parsers = argument_parser.add_subparsers(dest="command", required=True)
    command_parsers.add_parser("summary", help="show how many rows each input table has")
    command_parsers.add_parser("keys", help="show the identity keys of every company")
    command_parsers.add_parser("groups", help="show the duplicate groups and why each row is in them")
    arguments = argument_parser.parse_args()

    tables = load_tables(DATA_DIRECTORY)
    if arguments.command == "summary":
        print_summary(tables)
    elif arguments.command == "keys":
        print_identity_keys(tables["prospects"])
    elif arguments.command == "groups":
        duplicate_groups, review_items = find_duplicate_groups(tables["prospects"])
        print_duplicate_groups(duplicate_groups, review_items)


if __name__ == "__main__":
    main()
