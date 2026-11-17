"""Run with: python3 -m unittest -v"""
import unittest

from dedup import DATA_DIRECTORY, TABLE_NAMES, load_tables


class TestLoadTables(unittest.TestCase):

    def test_loads_the_nine_input_tables(self):
        tables = load_tables(DATA_DIRECTORY)

        self.assertEqual(sorted(tables.keys()), sorted(TABLE_NAMES))

    def test_loads_the_65_prospects_with_their_codes(self):
        tables = load_tables(DATA_DIRECTORY)

        prospect_codes = [prospect["prospect_code"] for prospect in tables["prospects"]]
        self.assertEqual(len(prospect_codes), 65)
        self.assertIn("P-000029", prospect_codes)

    def test_an_empty_cell_is_loaded_as_empty_text(self):
        tables = load_tables(DATA_DIRECTORY)

        cedar_without_phone = next(
            prospect for prospect in tables["prospects"]
            if prospect["prospect_code"] == "P-000032"
        )
        self.assertEqual(cedar_without_phone["phone"], "")


if __name__ == "__main__":
    unittest.main()
