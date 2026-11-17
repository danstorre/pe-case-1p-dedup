import unittest

from dedup.grouping import find_duplicate_groups


def make_prospect(prospect_code, website, phone):
    return {"prospect_code": prospect_code, "website": website, "phone": phone}


def prospect_codes_of_each_group(duplicate_groups):
    return [
        sorted(prospect["prospect_code"] for prospect in duplicate_group["prospects"])
        for duplicate_group in duplicate_groups
    ]


class TestRowsWithAWebsite(unittest.TestCase):

    def test_rows_with_the_same_root_domain_form_one_group(self):
        row_with_full_url = make_prospect("P-900001", "https://www.shop-a.com/", "212-555-0101")
        row_with_bare_domain = make_prospect("P-900002", "shop-a.com", "")

        duplicate_groups, review_items = find_duplicate_groups([row_with_full_url, row_with_bare_domain])

        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-900001", "P-900002"]])

    def test_rows_with_different_domains_are_not_grouped_even_if_they_share_a_phone(self):
        row_of_shop_a = make_prospect("P-900001", "https://shop-a.com", "212-555-0101")
        row_of_shop_b = make_prospect("P-900002", "https://shop-b.com", "212-555-0101")

        duplicate_groups, review_items = find_duplicate_groups([row_of_shop_a, row_of_shop_b])

        self.assertEqual(duplicate_groups, [])

    def test_a_row_whose_domain_appears_once_is_not_a_group(self):
        only_row_of_shop_a = make_prospect("P-900001", "https://shop-a.com", "212-555-0101")

        duplicate_groups, review_items = find_duplicate_groups([only_row_of_shop_a])

        self.assertEqual(duplicate_groups, [])


class TestRowsWithoutAWebsite(unittest.TestCase):

    def test_a_row_without_website_joins_the_group_that_has_its_main_phone(self):
        row_with_website = make_prospect("P-900001", "https://shop-a.com", "(212) 555-0101")
        row_without_website = make_prospect("P-900002", "", "212.555.0101")

        duplicate_groups, review_items = find_duplicate_groups([row_with_website, row_without_website])

        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-900001", "P-900002"]])

    def test_rows_without_website_and_the_same_main_phone_form_one_group(self):
        row_with_empty_website = make_prospect("P-900001", "", "(212) 555-0101")
        row_with_generic_website = make_prospect("P-900002", "gmail.com", "212.555.0101")

        duplicate_groups, review_items = find_duplicate_groups(
            [row_with_empty_website, row_with_generic_website]
        )

        self.assertEqual(prospect_codes_of_each_group(duplicate_groups), [["P-900001", "P-900002"]])
        self.assertEqual(review_items, [])

    def test_rows_with_a_generic_domain_and_different_phones_are_not_grouped(self):
        first_row_with_generic_website = make_prospect("P-900001", "gmail.com", "212-555-0101")
        second_row_with_generic_website = make_prospect("P-900002", "gmail.com", "212-555-0102")

        duplicate_groups, review_items = find_duplicate_groups(
            [first_row_with_generic_website, second_row_with_generic_website]
        )

        self.assertEqual(duplicate_groups, [])

    def test_a_group_of_three_records_how_each_row_got_in(self):
        row_with_website_only = make_prospect("P-900001", "https://www.shop-a.com", "")
        row_with_website_and_phone = make_prospect("P-900002", "https://shop-a.com", "212-555-0101")
        row_with_phone_only = make_prospect("P-900003", "", "212-555-0101")

        duplicate_groups, review_items = find_duplicate_groups(
            [row_with_website_only, row_with_website_and_phone, row_with_phone_only]
        )

        match_reasons = duplicate_groups[0]["match_reasons"]
        self.assertEqual(
            prospect_codes_of_each_group(duplicate_groups), [["P-900001", "P-900002", "P-900003"]]
        )
        self.assertEqual(match_reasons["P-900002"], "website domain shop-a.com")
        self.assertEqual(
            match_reasons["P-900003"], "no website; main phone 2125550101 belongs to shop-a.com"
        )


class TestRowsThatNeedAHuman(unittest.TestCase):

    def test_rows_without_website_or_phone_go_to_review_not_to_a_group(self):
        first_row_without_identity = make_prospect("P-900001", "", "")
        second_row_without_identity = make_prospect("P-900002", "", "")

        duplicate_groups, review_items = find_duplicate_groups(
            [first_row_without_identity, second_row_without_identity]
        )

        self.assertEqual(duplicate_groups, [])
        self.assertEqual(
            [review_item["prospect_code"] for review_item in review_items],
            ["P-900001", "P-900002"],
        )
        self.assertIn("no website and no main phone", review_items[0]["reason"])

    def test_a_row_whose_phone_belongs_to_several_domains_goes_to_review(self):
        row_of_shop_a = make_prospect("P-900001", "https://shop-a.com", "212-555-0101")
        row_of_shop_b = make_prospect("P-900002", "https://shop-b.com", "212-555-0101")
        row_with_only_that_phone = make_prospect("P-900003", "", "212-555-0101")

        duplicate_groups, review_items = find_duplicate_groups(
            [row_of_shop_a, row_of_shop_b, row_with_only_that_phone]
        )

        self.assertEqual(duplicate_groups, [])
        self.assertEqual(review_items[0]["prospect_code"], "P-900003")
        self.assertIn("shop-a.com, shop-b.com", review_items[0]["reason"])
