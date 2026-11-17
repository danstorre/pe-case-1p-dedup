"""Command line interface.

Usage:
    python3 -m dedup summary      show how many rows each input table has
    python3 -m dedup keys         show the identity keys of every company
    python3 -m dedup groups       show the duplicate groups and why each row is in them
    python3 -m dedup dry-run      append the attempts to output/merge_audit.csv, write nothing else
    python3 -m dedup apply        merge: write the merged tables and the audit to output/

Options: --data-dir (default data/) and --output-dir (default output/).
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from dedup.audit import replace_user_ids_with_names
from dedup.identity import phone_identity_key, website_identity_key
from dedup.output import AUDIT_FILE_NAME, write_merge_output
from dedup.plan import plan_merges, run_merge_plans
from dedup.tables import DATA_DIRECTORY, load_column_names, load_tables

OUTPUT_DIRECTORY = DATA_DIRECTORY.parent / "output"


def current_utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def print_summary(tables):
    for table_name, table_rows in tables.items():
        print(f"{table_name:<26} {len(table_rows):>3} rows")


def print_identity_keys(prospects):
    print(f"{'code':<9} {'shop name':<31} {'website key':<22} phone key")
    for prospect in prospects:
        website_key = website_identity_key(prospect["website"]) or "-"
        phone_key = phone_identity_key(prospect["phone"]) or "-"
        print(f"{prospect['prospect_code']:<9} {prospect['shop_name']:<31} {website_key:<22} {phone_key}")


def print_duplicate_groups(merge_plans, review_items, profiles):
    """Read-only view of the plan: every group, its survivor, and why a person has to decide."""
    groups_that_need_review = [merge_plan for merge_plan in merge_plans if merge_plan["blocker_reasons"]]
    groups_that_can_merge = len(merge_plans) - len(groups_that_need_review)
    print(
        f"DUPLICATE GROUPS ({len(merge_plans)}): "
        f"{groups_that_can_merge} can merge, {len(groups_that_need_review)} need review"
    )
    for merge_plan in merge_plans:
        group_decision = "NEEDS REVIEW" if merge_plan["blocker_reasons"] else "can merge"
        print(f"\n{merge_plan['identity_key']}  [{group_decision}]")
        prospects_survivor_first = [merge_plan["survivor"], *merge_plan["losers"]]
        if merge_plan["survivor"] is None:
            prospects_survivor_first = merge_plan["losers"]
        for prospect in prospects_survivor_first:
            survivor_mark = "survivor" if prospect is merge_plan["survivor"] else ""
            match_reason = merge_plan["match_reasons"][prospect["prospect_code"]]
            print(f"  {prospect['prospect_code']}  {prospect['shop_name']:<31} {survivor_mark:<9} {match_reason}")
        for blocker_reason in merge_plan["blocker_reasons"]:
            print(f"  reason: {replace_user_ids_with_names(blocker_reason, profiles)}")
    print(f"\nROWS THAT COULD NOT BE GROUPED ({len(review_items)})")
    for review_item in review_items:
        print(f"  {review_item['prospect_code']}  {review_item['reason']}")


def run_merges(data_directory, output_directory, is_dry_run, merge_timestamp):
    """Read data/, plan and run the merges on a copy, write output/, print what happened."""
    tables = load_tables(data_directory)
    merge_plans, review_items = plan_merges(tables["prospects"])
    merged_tables, audit_rows = run_merge_plans(tables, merge_plans, review_items, is_dry_run, merge_timestamp)
    write_merge_output(
        output_directory, data_directory, merged_tables, audit_rows, load_column_names(data_directory), is_dry_run
    )
    print_audit_rows(audit_rows, output_directory / AUDIT_FILE_NAME)


def print_audit_rows(audit_rows, audit_path):
    for audit_row in audit_rows:
        survivor_code = audit_row["survivor_code"] or "-"
        print(f"{audit_row['status']:<13} {survivor_code:<9} <- {audit_row['loser_code']:<9} {audit_row['details']}")
    status_counts = {}
    for audit_row in audit_rows:
        status_counts[audit_row["status"]] = status_counts.get(audit_row["status"], 0) + 1
    print("\n" + ", ".join(f"{count} {status}" for status, count in status_counts.items()) + f". Audit: {audit_path}")


def main(command_line_arguments=None, make_merge_timestamp=current_utc_timestamp):
    argument_parser = argparse.ArgumentParser(
        description="Find and merge duplicate companies in the 1P prospect database."
    )
    directory_options = argparse.ArgumentParser(add_help=False)
    directory_options.add_argument("--data-dir", type=Path, default=DATA_DIRECTORY, help="input CSV folder")
    directory_options.add_argument("--output-dir", type=Path, default=OUTPUT_DIRECTORY, help="output folder")
    command_parsers = argument_parser.add_subparsers(dest="command", required=True)
    for command_name, command_help in [
        ("summary", "show how many rows each input table has"),
        ("keys", "show the identity keys of every company"),
        ("groups", "show the duplicate groups and why each row is in them"),
        ("dry-run", "append the attempts to the audit, write nothing else"),
        ("apply", "merge: write the merged tables and the audit"),
    ]:
        command_parsers.add_parser(command_name, help=command_help, parents=[directory_options])
    arguments = argument_parser.parse_args(command_line_arguments)

    if arguments.command in ("dry-run", "apply"):
        is_dry_run = arguments.command == "dry-run"
        run_merges(arguments.data_dir, arguments.output_dir, is_dry_run, make_merge_timestamp())
        return

    tables = load_tables(arguments.data_dir)
    if arguments.command == "summary":
        print_summary(tables)
    elif arguments.command == "keys":
        print_identity_keys(tables["prospects"])
    elif arguments.command == "groups":
        merge_plans, review_items = plan_merges(tables["prospects"])
        print_duplicate_groups(merge_plans, review_items, tables["profiles"])
