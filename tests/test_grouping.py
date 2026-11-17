import unittest

from dedup.grouping import find_duplicate_groups


class FindDuplicateGroupsTests(unittest.TestCase):

    def test_find_duplicate_groups_delivers_nothing_on_empty_list(self):
        self.expect([], delivers_groups=[], delivers_review=[])

    def test_find_duplicate_groups_delivers_no_groups_on_a_single_row(self):
        single_row = make_prospect("P-900001", website="https://shop-a.com")

        self.expect([single_row], delivers_groups=[], delivers_review=[])

    def test_find_duplicate_groups_delivers_one_group_on_rows_with_the_same_root_domain(self):
        row_with_full_url = make_prospect("P-900001", website="https://www.shop-a.com/")
        row_with_bare_domain = make_prospect("P-900002", website="shop-a.com")

        self.expect(
            [row_with_full_url, row_with_bare_domain],
            delivers_groups=[["P-900001", "P-900002"]],
            delivers_review=[],
        )

    def test_find_duplicate_groups_delivers_no_groups_on_different_domains_sharing_a_phone(self):
        row_of_shop_a = make_prospect("P-900001", website="https://shop-a.com", phone=any_phone())
        row_of_shop_b = make_prospect("P-900002", website="https://shop-b.com", phone=any_phone())

        self.expect([row_of_shop_a, row_of_shop_b], delivers_groups=[], delivers_review=[])

    def test_find_duplicate_groups_delivers_row_without_website_in_the_group_that_owns_its_phone(self):
        row_with_website = make_prospect("P-900001", website="https://shop-a.com", phone="(212) 555-0101")
        row_without_website = make_prospect("P-900002", phone="212.555.0101")

        self.expect(
            [row_with_website, row_without_website],
            delivers_groups=[["P-900001", "P-900002"]],
            delivers_review=[],
        )

    def test_find_duplicate_groups_delivers_one_group_on_rows_without_website_sharing_a_phone(self):
        row_with_empty_website = make_prospect("P-900001", phone="(212) 555-0101")
        row_with_generic_website = make_prospect("P-900002", website="gmail.com", phone="212.555.0101")

        self.expect(
            [row_with_empty_website, row_with_generic_website],
            delivers_groups=[["P-900001", "P-900002"]],
            delivers_review=[],
        )

    def test_find_duplicate_groups_delivers_no_groups_on_generic_domains_with_different_phones(self):
        first_generic_row = make_prospect("P-900001", website="gmail.com", phone="212-555-0101")
        second_generic_row = make_prospect("P-900002", website="gmail.com", phone="212-555-0102")

        self.expect([first_generic_row, second_generic_row], delivers_groups=[], delivers_review=[])

    def test_find_duplicate_groups_delivers_how_each_row_got_into_the_group(self):
        row_with_website_only = make_prospect("P-900001", website="https://www.shop-a.com")
        row_with_website_and_phone = make_prospect("P-900002", website="https://shop-a.com", phone=any_phone())
        row_with_phone_only = make_prospect("P-900003", phone=any_phone())

        duplicate_groups, _ = find_duplicate_groups(
            [row_with_website_only, row_with_website_and_phone, row_with_phone_only]
        )

        match_reasons = duplicate_groups[0]["match_reasons"]
        self.assertEqual(match_reasons["P-900002"], "website domain shop-a.com")
        self.assertEqual(match_reasons["P-900003"], "no website; main phone 2125550101 belongs to shop-a.com")

    def test_find_duplicate_groups_delivers_review_items_on_rows_without_website_or_phone(self):
        first_row_without_identity = make_prospect("P-900001")
        second_row_without_identity = make_prospect("P-900002")

        self.expect(
            [first_row_without_identity, second_row_without_identity],
            delivers_groups=[],
            delivers_review=["P-900001", "P-900002"],
        )

    def test_find_duplicate_groups_delivers_review_item_on_phone_owned_by_several_domains(self):
        row_of_shop_a = make_prospect("P-900001", website="https://shop-a.com", phone=any_phone())
        row_of_shop_b = make_prospect("P-900002", website="https://shop-b.com", phone=any_phone())
        row_with_only_that_phone = make_prospect("P-900003", phone=any_phone())

        self.expect(
            [row_of_shop_a, row_of_shop_b, row_with_only_that_phone],
            delivers_groups=[],
            delivers_review=["P-900003"],
        )

    # Helpers

    def expect(self, prospects, delivers_groups, delivers_review):
        duplicate_groups, review_items = find_duplicate_groups(prospects)

        received_groups = [
            sorted(prospect["prospect_code"] for prospect in duplicate_group["prospects"])
            for duplicate_group in duplicate_groups
        ]
        received_review = [review_item["prospect_code"] for review_item in review_items]
        self.assertEqual(received_groups, delivers_groups)
        self.assertEqual(received_review, delivers_review)


def make_prospect(prospect_code, website="", phone=""):
    return {"prospect_code": prospect_code, "website": website, "phone": phone}


def any_phone():
    return "212-555-0101"
