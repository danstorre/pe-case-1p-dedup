"""Run with: python3 -m unittest -v"""
import unittest

from dedup import DATA_DIRECTORY, TABLE_NAMES, load_tables, website_identity_key


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


class TestWebsiteIdentityKey(unittest.TestCase):

    def test_removes_https_www_and_trailing_slash(self):
        self.assertEqual(website_identity_key("https://www.cedartool.com/"), "cedartool.com")

    def test_two_spellings_of_the_same_website_give_the_same_key(self):
        cedar_key_from_import = website_identity_key("https://www.cedartool.com/")
        cedar_key_typed_by_hand = website_identity_key("cedartool.com")

        self.assertEqual(cedar_key_from_import, cedar_key_typed_by_hand)

    def test_upper_case_and_spaces_do_not_change_the_key(self):
        self.assertEqual(website_identity_key("  HTTPS://CedarTool.com "), "cedartool.com")

    def test_page_path_query_and_port_are_not_part_of_the_key(self):
        website_with_extras = "https://www.cedartool.com:443/contact?source=import"

        self.assertEqual(website_identity_key(website_with_extras), "cedartool.com")

    def test_a_generic_email_domain_does_not_identify_a_company(self):
        self.assertIsNone(website_identity_key("gmail.com"))
        self.assertIsNone(website_identity_key("https://www.yahoo.com/"))

    def test_an_empty_website_has_no_key(self):
        self.assertIsNone(website_identity_key(""))
        self.assertIsNone(website_identity_key("   "))

    def test_text_that_is_not_a_website_has_no_key(self):
        self.assertIsNone(website_identity_key("n/a"))


if __name__ == "__main__":
    unittest.main()
