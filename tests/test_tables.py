import tempfile
import unittest
from functools import partial
from pathlib import Path

from dedup.tables import TABLE_NAMES, load_tables


class LoadTablesTests(unittest.TestCase):

    def test_load_tables_delivers_every_input_table(self):
        # Given
        sut = self.make_sut()

        # When
        tables = sut()

        # Then
        self.assertEqual(sorted(tables.keys()), sorted(TABLE_NAMES))

    def test_load_tables_delivers_each_row_as_a_dict_of_column_to_text(self):
        # Given
        sut = self.make_sut(prospects_csv_text="id,prospect_code,shop_name\nid-1,P-900001,Shop A\n")

        # When
        tables = sut()

        # Then
        self.assertEqual(
            tables["prospects"], [{"id": "id-1", "prospect_code": "P-900001", "shop_name": "Shop A"}]
        )

    def test_load_tables_delivers_empty_text_on_empty_cell(self):
        # Given
        sut = self.make_sut(prospects_csv_text="id,prospect_code,phone\nid-1,P-900001,\n")

        # When
        tables = sut()

        # Then
        self.assertEqual(tables["prospects"][0]["phone"], "")

    # Helpers

    def make_sut(self, prospects_csv_text="id\n"):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        data_directory = Path(temporary_directory.name)
        for table_name in TABLE_NAMES:
            (data_directory / f"{table_name}.csv").write_text("id\n")
        (data_directory / "prospects.csv").write_text(prospects_csv_text)
        return partial(load_tables, data_directory)
