"""Read the input CSV files. Nothing in this module writes to disk."""
import csv
from pathlib import Path

from dedup.schema import TABLE_NAMES

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"


def load_tables(data_directory):
    """Read every input CSV into memory. Each row becomes a dict of column -> text."""
    tables = {}
    for table_name in TABLE_NAMES:
        csv_path = data_directory / f"{table_name}.csv"
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            tables[table_name] = list(csv.DictReader(csv_file))
    return tables


def load_column_names(data_directory):
    """The header of every input CSV, in order, so the output keeps the same shape."""
    column_names_by_table = {}
    for table_name in TABLE_NAMES:
        csv_path = data_directory / f"{table_name}.csv"
        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            column_names_by_table[table_name] = next(csv.reader(csv_file))
    return column_names_by_table
