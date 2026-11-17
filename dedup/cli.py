"""Command line interface.

Usage:
    python3 -m dedup summary      show how many rows each input table has
    python3 -m dedup keys         show the identity keys of every company
    python3 -m dedup groups       show the duplicate groups and why each row is in them
"""
import argparse

from dedup.blockers import find_blockers
from dedup.grouping import find_duplicate_groups
from dedup.identity import phone_identity_key, website_identity_key
from dedup.survivor import choose_survivor
from dedup.tables import DATA_DIRECTORY, load_tables


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
        survivor = choose_survivor(duplicate_group["prospects"])
        print(f"\n{duplicate_group['identity_key']}")
        for prospect in duplicate_group["prospects"]:
            match_reason = duplicate_group["match_reasons"][prospect["prospect_code"]]
            survivor_mark = "survivor" if prospect is survivor else ""
            print(f"  {prospect['prospect_code']}  {prospect['shop_name']:<31} {survivor_mark:<9} {match_reason}")
        if survivor is None:
            print("  no survivor: every row already lost a merge")
        for blocker_reason in find_blockers(duplicate_group["prospects"]):
            print(f"  NEEDS REVIEW: {blocker_reason}")
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
