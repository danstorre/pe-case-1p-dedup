import csv
import tempfile
import unittest
from functools import partial
from pathlib import Path

from dedup.schema import AUDIT_COLUMN_NAMES
from dedup.write.output import write_merge_output
from dedup.schema import TABLE_NAMES


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

    def test_write_merge_output_writes_every_table_with_its_input_columns_on_a_real_run(self):
        # Given
        sut, output_directory, _ = self.make_sut()
        merged_tables = make_tables(prospect_contacts=[{"id": "contact-1", "prospect_id": "id-1"}])

        # When
        sut(merged_tables=merged_tables, audit_rows=[], is_dry_run=False)

        # Then
        for table_name in TABLE_NAMES:
            self.assertEqual(read_header(output_directory / f"{table_name}.csv"), ["id", "prospect_id"])
        self.assertEqual(
            read_rows(output_directory / "prospect_contacts.csv"), [{"id": "contact-1", "prospect_id": "id-1"}]
        )

    def test_write_merge_output_writes_only_the_audit_file_on_a_dry_run(self):
        # Given
        sut, output_directory, _ = self.make_sut()

        # When
        sut(merged_tables=make_tables(), audit_rows=[make_audit_row("request-1")], is_dry_run=True)

        # Then
        self.assertEqual(sorted(path.name for path in output_directory.iterdir()), ["merge_audit.csv"])

    def test_write_merge_output_appends_to_the_audit_trail_of_earlier_runs(self):
        # Given
        sut, output_directory, _ = self.make_sut()
        dry_run_audit_row = make_audit_row("request-1")
        real_run_audit_row = make_audit_row("request-2")

        # When
        sut(merged_tables=make_tables(), audit_rows=[dry_run_audit_row], is_dry_run=True)
        sut(merged_tables=make_tables(), audit_rows=[real_run_audit_row], is_dry_run=False)

        # Then
        self.assertEqual(read_rows(output_directory / "merge_audit.csv"), [dry_run_audit_row, real_run_audit_row])

    def test_write_merge_output_refuses_to_write_into_the_data_directory(self):
        # Given
        _, _, data_directory = self.make_sut()
        sut_pointed_at_data = partial(
            write_merge_output,
            data_directory,
            data_directory,
            column_names_by_table={table_name: ["id", "prospect_id"] for table_name in TABLE_NAMES},
        )

        # When / Then
        with self.assertRaises(ValueError):
            sut_pointed_at_data(merged_tables=make_tables(), audit_rows=[], is_dry_run=False)

    def test_write_merge_output_refuses_to_write_inside_the_data_directory(self):
        # Given
        _, _, data_directory = self.make_sut()
        sut_pointed_inside_data = partial(
            write_merge_output,
            data_directory / "output",
            data_directory,
            column_names_by_table={table_name: ["id", "prospect_id"] for table_name in TABLE_NAMES},
        )

        # When / Then
        with self.assertRaises(ValueError):
            sut_pointed_inside_data(merged_tables=make_tables(), audit_rows=[], is_dry_run=False)

    def test_write_merge_output_never_changes_the_files_in_the_data_directory(self):
        # Given
        sut, _, data_directory = self.make_sut()
        data_files_before = read_every_file(data_directory)
        merged_tables = make_tables(prospect_contacts=[{"id": "contact-1", "prospect_id": "id-2"}])

        # When
        sut(merged_tables=merged_tables, audit_rows=[make_audit_row("request-1")], is_dry_run=False)

        # Then
        self.assertEqual(read_every_file(data_directory), data_files_before)

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


def read_every_file(directory):
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}
