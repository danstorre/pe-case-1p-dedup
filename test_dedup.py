"""Run with: python3 -m unittest -v"""
import unittest

from dedup import (
    DATA_DIRECTORY,
    TABLE_NAMES,
    find_duplicate_groups,
    load_tables,
    phone_identity_key,
    website_identity_key,
)


def prospect_codes_of_each_group(duplicate_groups):
    return [
        sorted(prospect["prospect_code"] for prospect in duplicate_group["prospects"])
        for duplicate_group in duplicate_groups
    ]


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

    def test_a_subdomain_gives_the_root_domain(self):
        self.assertEqual(
            website_identity_key("https://waco.zenithstamping.com"), "zenithstamping.com"
        )

    def test_a_subdomain_of_a_generic_domain_has_no_key(self):
        self.assertIsNone(website_identity_key("https://mail.yahoo.com"))

    def test_a_generic_email_domain_does_not_identify_a_company(self):
        self.assertIsNone(website_identity_key("gmail.com"))
        self.assertIsNone(website_identity_key("https://www.yahoo.com/"))

    def test_an_empty_website_has_no_key(self):
        self.assertIsNone(website_identity_key(""))
        self.assertIsNone(website_identity_key("   "))

    def test_text_that_is_not_a_website_has_no_key(self):
        self.assertIsNone(website_identity_key("n/a"))


class TestPhoneIdentityKey(unittest.TestCase):

    def test_two_formats_of_the_same_phone_give_the_same_key(self):
        granite_phone_with_dots = phone_identity_key("814.555.0199")
        granite_phone_with_parentheses = phone_identity_key("(814) 555-0199")

        self.assertEqual(granite_phone_with_dots, "8145550199")
        self.assertEqual(granite_phone_with_parentheses, "8145550199")

    def test_the_us_country_code_is_not_part_of_the_key(self):
        self.assertEqual(phone_identity_key("+1 814-555-0199"), "8145550199")

    def test_an_empty_phone_has_no_key(self):
        self.assertIsNone(phone_identity_key(""))

    def test_a_phone_without_ten_digits_has_no_key(self):
        self.assertIsNone(phone_identity_key("555-0199"))


class TestFindDuplicateGroups(unittest.TestCase):

    def setUp(self):
        all_prospects = load_tables(DATA_DIRECTORY)["prospects"]
        self.duplicate_groups, self.review_items = find_duplicate_groups(all_prospects)
        self.codes_of_each_group = prospect_codes_of_each_group(self.duplicate_groups)

    def test_cedar_rows_with_the_same_website_domain_are_one_group(self):
        self.assertIn(["P-000029", "P-000032"], self.codes_of_each_group)

    def test_a_company_that_appears_once_is_not_a_group(self):
        alder_metal_code = "P-000001"

        for codes_in_group in self.codes_of_each_group:
            self.assertNotIn(alder_metal_code, codes_in_group)

    def test_vista_and_timber_share_a_phone_but_not_a_website_so_they_are_not_grouped(self):
        for codes_in_group in self.codes_of_each_group:
            self.assertNotIn("P-000007", codes_in_group)
            self.assertNotIn("P-000054", codes_in_group)


if __name__ == "__main__":
    unittest.main()
