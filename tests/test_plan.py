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
