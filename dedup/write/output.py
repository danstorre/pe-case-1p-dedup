"""Write the result to output/. This is the only module that writes files, and never into data/."""
import csv

from dedup.schema import AUDIT_COLUMN_NAMES
from dedup.schema import TABLE_NAMES

AUDIT_FILE_NAME = "merge_audit.csv"


def write_merge_output(
    output_directory, data_directory, merged_tables, audit_rows, column_names_by_table, is_dry_run
):
    """Append the audit rows and, on a real run, write every merged table. Never writes into data/."""
    refuse_to_write_into(data_directory, output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    append_audit_rows(output_directory / AUDIT_FILE_NAME, audit_rows)
    if is_dry_run:
        return
    for table_name in TABLE_NAMES:
        write_csv(
            output_directory / f"{table_name}.csv", column_names_by_table[table_name], merged_tables[table_name]
        )


def write_csv(csv_path, column_names, rows):
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=column_names)
        csv_writer.writeheader()
        csv_writer.writerows(rows)


def append_audit_rows(audit_path, audit_rows):
    """The audit trail only grows: every run, dry or real, adds its attempts."""
    audit_file_is_new = not audit_path.exists()
    with open(audit_path, "a", newline="", encoding="utf-8") as audit_file:
        csv_writer = csv.DictWriter(audit_file, fieldnames=AUDIT_COLUMN_NAMES)
        if audit_file_is_new:
            csv_writer.writeheader()
        csv_writer.writerows(audit_rows)


def refuse_to_write_into(data_directory, output_directory):
    """The input files in data/ must never be modified."""
    resolved_data_directory = data_directory.resolve()
    resolved_output_directory = output_directory.resolve()
    output_is_the_data_directory = resolved_output_directory == resolved_data_directory
    output_is_inside_the_data_directory = resolved_data_directory in resolved_output_directory.parents
    if output_is_the_data_directory or output_is_inside_the_data_directory:
        raise ValueError(f"refusing to write into the input data directory: {output_directory}")
