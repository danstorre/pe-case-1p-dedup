import tempfile
import unittest
from pathlib import Path

from dedup.tables import TABLE_NAMES, load_tables

PROSPECTS_CSV_TEXT = """id,prospect_code,shop_name,phone
id-1,P-900001,Shop A,212-555-0101
id-2,P-900002,Shop A Inc,
"""


class TestLoadTables(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.data_directory = Path(self.temporary_directory.name)
        for table_name in TABLE_NAMES:
            (self.data_directory / f"{table_name}.csv").write_text("id\n")
        (self.data_directory / "prospects.csv").write_text(PROSPECTS_CSV_TEXT)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_every_input_table_is_loaded(self):
        tables = load_tables(self.data_directory)

        self.assertEqual(sorted(tables.keys()), sorted(TABLE_NAMES))

    def test_each_csv_row_becomes_a_dict_of_column_to_text(self):
        tables = load_tables(self.data_directory)

        first_prospect = tables["prospects"][0]
        self.assertEqual(first_prospect["prospect_code"], "P-900001")
        self.assertEqual(first_prospect["shop_name"], "Shop A")

    def test_an_empty_cell_is_loaded_as_empty_text(self):
        tables = load_tables(self.data_directory)

        prospect_without_phone = tables["prospects"][1]
        self.assertEqual(prospect_without_phone["phone"], "")
