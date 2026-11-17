import csv
import tempfile
import unittest
from functools import partial
from pathlib import Path

from dedup.audit import AUDIT_COLUMN_NAMES
from dedup.output import write_merge_output
from dedup.tables import TABLE_NAMES


class WriteMergeOutputTests(unittest.TestCase):

    def test_write_merge_output_writes_the_audit_file_with_the_audit_columns(self):
        # Given
        sut, output_directory, _ = self.make_sut()
        audit_row = make_audit_row("request-1")

        # When
        sut(merged_tables=make_tables(), audit_rows=[audit_row], is_dry_run=False)

        # Then
        audit_file = output_directory / "merge_audit.csv"
        self.assertEqual(read_header(audit_file), AUDIT_COLUMN_NAMES)
        self.assertEqual(read_rows(audit_file), [audit_row])

    # Helpers

    def make_sut(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        data_directory = Path(temporary_directory.name) / "data"
        output_directory = Path(temporary_directory.name) / "output"
        data_directory.mkdir()
        for table_name in TABLE_NAMES:
            (data_directory / f"{table_name}.csv").write_text("id,prospect_id\r\n")
        sut = partial(
            write_merge_output,
            output_directory,
            data_directory,
            column_names_by_table={table_name: ["id", "prospect_id"] for table_name in TABLE_NAMES},
        )
        return sut, output_directory, data_directory


# Shared helpers

def make_tables(**rows_by_table_name):
    tables = {table_name: [] for table_name in TABLE_NAMES}
    tables.update(rows_by_table_name)
    return tables


def make_audit_row(request_id):
    return {
        "request_id": request_id,
        "survivor_code": "P-900001",
        "loser_code": "P-900002",
        "dry_run": "false",
        "status": "merged",
        "details": "website domain shop-a.com",
    }


def read_header(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return next(csv.reader(csv_file))


def read_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))
