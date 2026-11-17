import tempfile
import unittest
from functools import partial
from pathlib import Path

from dedup.tables import TABLE_NAMES, load_column_names, load_tables


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
        data_directory = make_data_directory(self, prospects_csv_text)
        return partial(load_tables, data_directory)


class LoadColumnNamesTests(unittest.TestCase):

    def test_load_column_names_delivers_the_header_of_every_table_in_order(self):
        # Given
        sut = self.make_sut(prospects_csv_text="id,prospect_code,shop_name\nid-1,P-900001,Shop A\n")

        # When
        column_names_by_table = sut()

        # Then
        self.assertEqual(sorted(column_names_by_table.keys()), sorted(TABLE_NAMES))
        self.assertEqual(column_names_by_table["prospects"], ["id", "prospect_code", "shop_name"])

    def test_load_column_names_delivers_the_header_of_a_table_without_rows(self):
        # Given
        sut = self.make_sut(prospects_csv_text="id,prospect_code\n")

        # When
        column_names_by_table = sut()

        # Then
        self.assertEqual(column_names_by_table["prospects"], ["id", "prospect_code"])

    # Helpers

    def make_sut(self, prospects_csv_text):
        data_directory = make_data_directory(self, prospects_csv_text)
        return partial(load_column_names, data_directory)


def make_data_directory(test_case, prospects_csv_text):
    temporary_directory = tempfile.TemporaryDirectory()
    test_case.addCleanup(temporary_directory.cleanup)
    data_directory = Path(temporary_directory.name)
    for table_name in TABLE_NAMES:
        (data_directory / f"{table_name}.csv").write_text("id\n")
    (data_directory / "prospects.csv").write_text(prospects_csv_text)
    return data_directory
