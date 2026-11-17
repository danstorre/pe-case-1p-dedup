import unittest

from dedup.plan import plan_merges


class PlanMergesTests(unittest.TestCase):

    def test_plan_merges_delivers_nothing_on_no_prospects(self):
        # Given
        sut = self.make_sut()

        # When
        merge_plans, review_items = sut([])

        # Then
        self.assertEqual(merge_plans, [])
        self.assertEqual(review_items, [])

    def test_plan_merges_delivers_the_survivor_and_losers_of_a_duplicate_group(self):
        # Given
        sut = self.make_sut()
        survivor_further_along = make_prospect("P-900001", website="https://shop-a.com", status="contacted")
        loser_not_yet_contacted = make_prospect("P-900002", website="shop-a.com")

        # When
        merge_plans, _ = sut([loser_not_yet_contacted, survivor_further_along])

        # Then
        self.assertEqual(len(merge_plans), 1)
        self.assertEqual(merge_plans[0]["survivor"]["prospect_code"], "P-900001")
        self.assertEqual(
            [loser["prospect_code"] for loser in merge_plans[0]["losers"]], ["P-900002"]
        )
        self.assertEqual(merge_plans[0]["blocker_reasons"], [])

    def test_plan_merges_delivers_the_blocker_reasons_of_a_group_a_person_has_to_decide(self):
        # Given
        sut = self.make_sut()
        row_of_first_sdr = make_prospect("P-900001", website="https://shop-a.com", tusdr_assigned_user_id="sdr-1")
        row_of_second_sdr = make_prospect("P-900002", website="shop-a.com", tusdr_assigned_user_id="sdr-2")

        # When
        merge_plans, _ = sut([row_of_first_sdr, row_of_second_sdr])

        # Then
        self.assertEqual(len(merge_plans[0]["blocker_reasons"]), 1)
        self.assertIn("different SDRs", merge_plans[0]["blocker_reasons"][0])

    def test_plan_merges_delivers_a_blocker_when_no_row_can_survive(self):
        # Given
        sut = self.make_sut()
        first_row_that_lost_a_merge = make_prospect("P-900001", website="https://shop-a.com", merged_into_id="id-9")
        second_row_that_lost_a_merge = make_prospect("P-900002", website="shop-a.com", merged_into_id="id-9")

        # When
        merge_plans, _ = sut([first_row_that_lost_a_merge, second_row_that_lost_a_merge])

        # Then
        self.assertIsNone(merge_plans[0]["survivor"])
        self.assertIn("no row can survive", merge_plans[0]["blocker_reasons"][0])

    def test_plan_merges_delivers_the_review_items_of_rows_that_cannot_be_grouped(self):
        # Given
        sut = self.make_sut()
        row_without_website_or_phone = make_prospect("P-900001")

        # When
        merge_plans, review_items = sut([row_without_website_or_phone])

        # Then
        self.assertEqual(merge_plans, [])
        self.assertEqual([review_item["prospect_code"] for review_item in review_items], ["P-900001"])

    # Helpers

    def make_sut(self):
        return plan_merges


# Shared helpers

def make_prospect(prospect_code, **fields):
    prospect = {
        "id": f"id-{prospect_code}",
        "prospect_code": prospect_code,
        "shop_name": f"Shop {prospect_code}",
        "website": "",
        "phone": "",
        "phone_secondary": "",
        "email": "",
        "email_secondary": "",
        "email_tertiary": "",
        "city": "",
        "state": "",
        "employee_count": "",
        "status": "not_yet_contacted",
        "tusdr_assigned_user_id": "",
        "record_source": "",
        "created_at": "2026-07-01T00:00:00+00:00",
        "updated_at": "",
        "merged_into_id": "",
        "archived_at": "",
    }
    prospect.update(fields)
    return prospect
