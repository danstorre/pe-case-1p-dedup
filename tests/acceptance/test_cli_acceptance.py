"""Acceptance tests: run the CLI end to end on a small invented CRM written to a temporary folder."""
import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from dedup.cli import main

MERGE_TIMESTAMP = "2026-11-18T12:00:00+00:00"

INPUT_COLUMN_NAMES = {
    "profiles": ["id", "display_name", "role"],
    "prospects": [
        "id", "prospect_code", "shop_name", "website", "phone", "phone_secondary", "email",
        "email_secondary", "email_tertiary", "city", "state", "employee_count", "status",
        "tusdr_assigned_user_id", "record_source", "created_at", "updated_at", "merged_into_id",
        "archived_at",
    ],
    "prospect_aliases": ["id", "prospect_id", "alias", "kind"],
    "prospect_contacts": ["id", "prospect_id", "full_name", "title", "email", "mobile", "lead_status", "do_not_call"],
    "sdr_follow_up_tasks": [
        "id", "prospect_id", "contact_id", "assignee_user_id", "task_type", "status", "note",
        "due_at", "completed_at", "created_at",
    ],
    "power_dialer_call_logs": [
        "id", "prospect_id", "contact_id", "user_id", "number_dialed", "outcome", "duration_sec", "called_at",
    ],
    "email_activities": ["id", "prospect_id", "contact_id", "user_id", "to_address", "subject", "sent_at"],
    "prospect_contact_notes": ["id", "prospect_id", "contact_id", "author_user_id", "body", "created_at"],
    "prospect_meetings": ["id", "prospect_id", "contact_id", "booked_by", "scheduled_at", "status"],
}


class PlanCommandAcceptanceTests(unittest.TestCase):

    def test_plan_writes_only_the_audit_and_changes_no_data(self):
        # Given
        data_directory, output_directory = self.make_directories_with_invented_crm()

        # When
        run_cli(["plan", "--data-dir", str(data_directory), "--output-dir", str(output_directory)])

        # Then
        self.assertEqual(sorted(path.name for path in output_directory.iterdir()), ["merge_audit.csv"])
        self.assertEqual(
            audit_summary(output_directory),
            [("P-900001", "P-900002", "true", "planned"), ("P-900003", "P-900004", "true", "needs_review")],
        )

    # Helpers

    def make_directories_with_invented_crm(self):
        return make_directories_with_invented_crm(self)


class ApplyCommandAcceptanceTests(unittest.TestCase):

    def test_apply_merges_a_duplicate_and_audits_it(self):
        # Given
        data_directory, output_directory = self.make_directories_with_invented_crm()

        # When
        run_cli(["apply", "--data-dir", str(data_directory), "--output-dir", str(output_directory)])

        # Then
        merged_loser = find_row(output_directory, "prospects", prospect_code="P-900002")
        self.assertEqual(merged_loser["merged_into_id"], "id-1")
        self.assertEqual(merged_loser["archived_at"], MERGE_TIMESTAMP)
        self.assertEqual(
            audit_summary(output_directory),
            [("P-900001", "P-900002", "false", "merged"), ("P-900003", "P-900004", "false", "needs_review")],
        )

    def test_apply_keeps_pending_tasks_do_not_call_contacts_and_booked_meetings(self):
        # Given
        data_directory, output_directory = self.make_directories_with_invented_crm()

        # When
        run_cli(["apply", "--data-dir", str(data_directory), "--output-dir", str(output_directory)])

        # Then
        pending_task = find_row(output_directory, "sdr_follow_up_tasks", id="task-1")
        do_not_call_contact = find_row(output_directory, "prospect_contacts", id="contact-1")
        booked_meeting = find_row(output_directory, "prospect_meetings", id="meeting-1")
        self.assertEqual((pending_task["prospect_id"], pending_task["status"]), ("id-1", "pending"))
        self.assertEqual((do_not_call_contact["prospect_id"], do_not_call_contact["do_not_call"]), ("id-1", "true"))
        self.assertEqual((booked_meeting["prospect_id"], booked_meeting["status"]), ("id-1", "scheduled"))

    def test_apply_keeps_the_old_name_searchable_as_an_alias(self):
        # Given
        data_directory, output_directory = self.make_directories_with_invented_crm()

        # When
        run_cli(["apply", "--data-dir", str(data_directory), "--output-dir", str(output_directory)])

        # Then
        self.assertEqual(
            [(alias_row["prospect_id"], alias_row["alias"]) for alias_row in read_rows(output_directory, "prospect_aliases")],
            [("id-1", "Shop A Inc")],
        )

    def test_apply_leaves_a_company_owned_by_two_sdrs_untouched_and_names_them(self):
        # Given
        data_directory, output_directory = self.make_directories_with_invented_crm()

        # When
        run_cli(["apply", "--data-dir", str(data_directory), "--output-dir", str(output_directory)])

        # Then
        self.assertEqual(
            find_row(output_directory, "prospects", prospect_code="P-900004"),
            find_row(data_directory, "prospects", prospect_code="P-900004"),
        )
        blocked_audit_row = read_rows(output_directory, "merge_audit")[1]
        self.assertIn("First Rep", blocked_audit_row["details"])
        self.assertIn("Second Rep", blocked_audit_row["details"])

    def test_apply_never_deletes_a_row_and_never_changes_the_data_directory(self):
        # Given
        data_directory, output_directory = self.make_directories_with_invented_crm()
        data_files_before = {path.name: path.read_bytes() for path in data_directory.iterdir()}

        # When
        run_cli(["apply", "--data-dir", str(data_directory), "--output-dir", str(output_directory)])

        # Then
        self.assertEqual({path.name: path.read_bytes() for path in data_directory.iterdir()}, data_files_before)
        for table_name in INPUT_COLUMN_NAMES:
            if table_name == "prospect_aliases":
                continue
            self.assertEqual(
                len(read_rows(output_directory, table_name)), len(read_rows(data_directory, table_name)), table_name
            )

    # Helpers

    def make_directories_with_invented_crm(self):
        return make_directories_with_invented_crm(self)


# Shared helpers

def run_cli(command_line_arguments):
    printed_output = io.StringIO()
    with contextlib.redirect_stdout(printed_output):
        main(command_line_arguments, make_merge_timestamp=fixed_merge_timestamp)
    return printed_output.getvalue()


def fixed_merge_timestamp():
    return MERGE_TIMESTAMP


def make_directories_with_invented_crm(test_case):
    temporary_directory = tempfile.TemporaryDirectory()
    test_case.addCleanup(temporary_directory.cleanup)
    data_directory = Path(temporary_directory.name) / "data"
    output_directory = Path(temporary_directory.name) / "output"
    data_directory.mkdir()
    write_invented_crm(data_directory)
    return data_directory, output_directory


def write_invented_crm(data_directory):
    """Shop A is a clean duplicate, Shop B is owned by two SDRs, Shop C appears once."""
    rows_by_table = {
        "profiles": [
            {"id": "sdr-1", "display_name": "First Rep", "role": "sdr"},
            {"id": "sdr-2", "display_name": "Second Rep", "role": "sdr"},
        ],
        "prospects": [
            make_prospect_row("id-1", "P-900001", "Shop A", "https://www.shop-a.com/", status="contacted", sdr="sdr-1"),
            make_prospect_row("id-2", "P-900002", "Shop A Inc", "shop-a.com"),
            make_prospect_row("id-3", "P-900003", "Shop B", "https://shop-b.com", status="contacted", sdr="sdr-1"),
            make_prospect_row("id-4", "P-900004", "Shop B LLC", "shop-b.com", sdr="sdr-2"),
            make_prospect_row("id-5", "P-900005", "Shop C", "https://shop-c.com"),
        ],
        "prospect_contacts": [
            {"id": "contact-1", "prospect_id": "id-2", "full_name": "Contact One", "lead_status": "do_not_contact", "do_not_call": "true"},
        ],
        "sdr_follow_up_tasks": [
            {"id": "task-1", "prospect_id": "id-2", "assignee_user_id": "sdr-1", "task_type": "schedule_callback", "status": "pending"},
        ],
        "prospect_meetings": [
            {"id": "meeting-1", "prospect_id": "id-2", "booked_by": "sdr-1", "status": "scheduled"},
        ],
    }
    for table_name, column_names in INPUT_COLUMN_NAMES.items():
        with open(data_directory / f"{table_name}.csv", "w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=column_names, restval="")
            csv_writer.writeheader()
            csv_writer.writerows(rows_by_table.get(table_name, []))


def make_prospect_row(prospect_id, prospect_code, shop_name, website, status="not_yet_contacted", sdr=""):
    return {
        "id": prospect_id,
        "prospect_code": prospect_code,
        "shop_name": shop_name,
        "website": website,
        "status": status,
        "tusdr_assigned_user_id": sdr,
        "created_at": "2026-07-01T00:00:00+00:00",
    }


def read_rows(directory, table_name):
    with open(directory / f"{table_name}.csv", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def find_row(directory, table_name, **expected_values):
    return next(
        row for row in read_rows(directory, table_name)
        if all(row[column_name] == value for column_name, value in expected_values.items())
    )


def audit_summary(output_directory):
    return [
        (audit_row["survivor_code"], audit_row["loser_code"], audit_row["dry_run"], audit_row["status"])
        for audit_row in read_rows(output_directory, "merge_audit")
    ]
