import tempfile
import unittest
from pathlib import Path

from dedup.tables import TABLE_NAMES, load_tables

PROSPECTS_CSV_TEXT = """id,prospect_code,shop_name,phone
id-29,P-000029,Cedar Tool & Die,937-555-0172
id-32,P-000032,Cedar Tool and Die Co.,
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

    def test_loads_every_input_table(self):
        tables = load_tables(self.data_directory)

        self.assertEqual(sorted(tables.keys()), sorted(TABLE_NAMES))

    def test_each_row_becomes_a_dict_of_column_to_text(self):
        tables = load_tables(self.data_directory)

        cedar_from_import = tables["prospects"][0]
        self.assertEqual(cedar_from_import["prospect_code"], "P-000029")
        self.assertEqual(cedar_from_import["shop_name"], "Cedar Tool & Die")

    def test_an_empty_cell_is_loaded_as_empty_text(self):
        tables = load_tables(self.data_directory)

        cedar_without_phone = tables["prospects"][1]
        self.assertEqual(cedar_without_phone["phone"], "")
