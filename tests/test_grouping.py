import unittest

from dedup.grouping import find_duplicate_groups


def prospect_codes_of_each_group(duplicate_groups):
    return [
        sorted(prospect["prospect_code"] for prospect in duplicate_group["prospects"])
        for duplicate_group in duplicate_groups
    ]


def make_prospect(prospect_code, website, phone):
    return {"prospect_code": prospect_code, "website": website, "phone": phone}


class TestFindDuplicateGroups(unittest.TestCase):

    def test_cedar_rows_with_the_same_website_domain_are_one_group(self):
        cedar_from_import = make_prospect("P-000029", "https://www.cedartool.com/", "937-555-0172")
        cedar_typed_by_hand = make_prospect("P-000032", "cedartool.com", "")

        duplicate_groups, review_items = find_duplicate_groups([cedar_from_import, cedar_typed_by_hand])

        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-000029", "P-000032"]])

    def test_granite_row_without_website_joins_the_group_that_has_its_main_phone(self):
        granite_with_website = make_prospect("P-000025", "https://granitecastings.net", "(814) 555-0199")
        granite_without_website = make_prospect("P-000006", "", "814.555.0199")

        duplicate_groups, review_items = find_duplicate_groups([granite_with_website, granite_without_website])

        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-000006", "P-000025"]])

    def test_summit_is_one_group_of_three_and_each_row_says_how_it_got_in(self):
        summit_without_phone = make_prospect("P-000017", "https://www.summitlaser.com", "")
        summit_without_website = make_prospect("P-000018", "", "815-555-0110")
        summit_with_both = make_prospect("P-000057", "https://summitlaser.com", "815-555-0110")

        duplicate_groups, review_items = find_duplicate_groups(
            [summit_without_phone, summit_without_website, summit_with_both]
        )

        summit_group = duplicate_groups[0]
        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-000017", "P-000018", "P-000057"]])
        self.assertEqual(summit_group["match_reasons"]["P-000057"], "website domain summitlaser.com")
        self.assertEqual(
            summit_group["match_reasons"]["P-000018"],
            "no website; main phone 8155550110 belongs to summitlaser.com",
        )

    def test_vista_and_timber_share_a_phone_but_not_a_website_so_they_are_not_grouped(self):
        vista_composites = make_prospect("P-000007", "https://vistacomposites.com", "208-555-0177")
        timber_gear = make_prospect("P-000054", "https://timbergear.com", "208-555-0177")

        duplicate_groups, review_items = find_duplicate_groups([vista_composites, timber_gear])

        self.assertEqual(duplicate_groups, [])

    def test_two_companies_with_a_gmail_website_and_different_phones_are_not_grouped(self):
        oak_street_welding = make_prospect("P-000047", "gmail.com", "478-555-0183")
        pioneer_mold_shop = make_prospect("P-000053", "gmail.com", "810-555-0144")

        duplicate_groups, review_items = find_duplicate_groups([oak_street_welding, pioneer_mold_shop])

        self.assertEqual(duplicate_groups, [])

    def test_a_company_that_appears_once_is_not_a_group(self):
        alder_metal = make_prospect("P-000001", "https://aldermetal.com", "787-911-6203")

        duplicate_groups, review_items = find_duplicate_groups([alder_metal])

        self.assertEqual(duplicate_groups, [])


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
