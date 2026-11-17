import unittest

from dedup.grouping import find_duplicate_groups
from dedup.tables import DATA_DIRECTORY, load_tables


def prospect_codes_of_each_group(duplicate_groups):
    return [
        sorted(prospect["prospect_code"] for prospect in duplicate_group["prospects"])
        for duplicate_group in duplicate_groups
    ]


def make_prospect(prospect_code, website, phone):
    return {"prospect_code": prospect_code, "website": website, "phone": phone}


class TestFindDuplicateGroups(unittest.TestCase):

    def setUp(self):
        all_prospects = load_tables(DATA_DIRECTORY)["prospects"]
        self.duplicate_groups, self.review_items = find_duplicate_groups(all_prospects)
        self.codes_of_each_group = prospect_codes_of_each_group(self.duplicate_groups)

    def test_cedar_rows_with_the_same_website_domain_are_one_group(self):
        self.assertIn(["P-000029", "P-000032"], self.codes_of_each_group)

    def test_granite_row_without_website_joins_the_group_that_has_its_main_phone(self):
        self.assertIn(["P-000006", "P-000025"], self.codes_of_each_group)

    def test_summit_is_one_group_of_three(self):
        self.assertIn(["P-000017", "P-000018", "P-000057"], self.codes_of_each_group)

    def test_the_match_reason_says_how_each_row_got_into_the_group(self):
        summit_group = next(
            duplicate_group for duplicate_group in self.duplicate_groups
            if duplicate_group["identity_key"] == "summitlaser.com"
        )

        self.assertEqual(summit_group["match_reasons"]["P-000057"], "website domain summitlaser.com")
        self.assertEqual(
            summit_group["match_reasons"]["P-000018"],
            "no website; main phone 8155550110 belongs to summitlaser.com",
        )

    def test_two_companies_with_a_gmail_website_and_different_phones_are_not_grouped(self):
        for codes_in_group in self.codes_of_each_group:
            self.assertNotIn("P-000047", codes_in_group)
            self.assertNotIn("P-000053", codes_in_group)

    def test_a_company_that_appears_once_is_not_a_group(self):
        alder_metal_code = "P-000001"

        for codes_in_group in self.codes_of_each_group:
            self.assertNotIn(alder_metal_code, codes_in_group)

    def test_vista_and_timber_share_a_phone_but_not_a_website_so_they_are_not_grouped(self):
        for codes_in_group in self.codes_of_each_group:
            self.assertNotIn("P-000007", codes_in_group)
            self.assertNotIn("P-000054", codes_in_group)


class TestCompaniesThatCannotBeGroupedSafely(unittest.TestCase):

    def test_companies_without_website_or_phone_are_never_grouped_together(self):
        first_company_without_identity = make_prospect("P-900001", "", "")
        second_company_without_identity = make_prospect("P-900002", "", "")

        duplicate_groups, review_items = find_duplicate_groups(
            [first_company_without_identity, second_company_without_identity]
        )

        self.assertEqual(duplicate_groups, [])
        self.assertEqual(
            [review_item["prospect_code"] for review_item in review_items],
            ["P-900001", "P-900002"],
        )
        self.assertIn("no website and no main phone", review_items[0]["reason"])

    def test_a_phone_used_by_two_different_companies_needs_a_human(self):
        vista_composites = make_prospect("P-000007", "https://vistacomposites.com", "208-555-0177")
        timber_gear = make_prospect("P-000054", "https://timbergear.com", "208-555-0177")
        company_with_only_that_phone = make_prospect("P-900003", "", "208-555-0177")

        duplicate_groups, review_items = find_duplicate_groups(
            [vista_composites, timber_gear, company_with_only_that_phone]
        )

        self.assertEqual(duplicate_groups, [])
        self.assertEqual(review_items[0]["prospect_code"], "P-900003")
        self.assertIn("timbergear.com, vistacomposites.com", review_items[0]["reason"])

    def test_two_companies_without_website_and_the_same_phone_are_one_group(self):
        first_row_of_the_shop = make_prospect("P-900004", "", "(478) 555-0100")
        second_row_of_the_shop = make_prospect("P-900005", "gmail.com", "478.555.0100")

        duplicate_groups, review_items = find_duplicate_groups(
            [first_row_of_the_shop, second_row_of_the_shop]
        )

        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-900004", "P-900005"]])
        self.assertEqual(review_items, [])
