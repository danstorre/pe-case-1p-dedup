import unittest
from functools import partial

from dedup.tables import TABLE_NAMES
from dedup.plan import (
    plan_merges,
    run_merge_plans,
)


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


class RunMergePlansTests(unittest.TestCase):

    def test_run_merge_plans_delivers_no_audit_rows_on_no_plans(self):
        # Given
        sut = self.make_sut()
        tables = make_tables()

        # When
        _, audit_rows = sut(tables, merge_plans=[], review_items=[], is_dry_run=False)

        # Then
        self.assertEqual(audit_rows, [])

    def test_run_merge_plans_merges_a_group_and_audits_it_as_merged(self):
        # Given
        sut = self.make_sut()
        survivor = make_prospect("P-900001", shop_name="Shop A")
        loser = make_prospect("P-900002", shop_name="Shop A Inc", phone="212-555-0101")
        contact_of_loser = {"id": "contact-1", "prospect_id": loser["id"]}
        tables = make_tables(prospects=[survivor, loser], prospect_contacts=[contact_of_loser])

        # When
        merged_tables, audit_rows = sut(
            tables, [make_merge_plan(survivor, [loser])], review_items=[], is_dry_run=False
        )

        # Then
        merged_survivor, merged_loser = merged_tables["prospects"]
        self.assertEqual(merged_tables["prospect_contacts"][0]["prospect_id"], survivor["id"])
        self.assertEqual(merged_survivor["phone"], "212-555-0101")
        self.assertEqual(merged_loser["merged_into_id"], survivor["id"])
        self.assertEqual(merged_loser["archived_at"], MERGE_TIMESTAMP)
        self.assertEqual(audit_rows, [{
            "request_id": "new-id",
            "survivor_code": "P-900001",
            "loser_code": "P-900002",
            "dry_run": "false",
            "status": "merged",
            "details": "website domain shop-a.com; moved 1 prospect_contacts; "
                       "filled phone=212-555-0101; added alias 'Shop A Inc'",
        }])

    def test_run_merge_plans_audits_merges_as_planned_on_a_dry_run(self):
        # Given
        sut = self.make_sut()
        survivor, loser = make_prospect("P-900001"), make_prospect("P-900002")
        tables = make_tables(prospects=[survivor, loser])

        # When
        _, audit_rows = sut(tables, [make_merge_plan(survivor, [loser])], review_items=[], is_dry_run=True)

        # Then
        self.assertEqual(audit_rows[0]["dry_run"], "true")
        self.assertEqual(audit_rows[0]["status"], "planned")

    def test_run_merge_plans_leaves_a_blocked_group_untouched_and_audits_it_as_needs_review(self):
        # Given
        sut = self.make_sut()
        survivor = make_prospect("P-900001", tusdr_assigned_user_id="sdr-1")
        loser = make_prospect("P-900002", tusdr_assigned_user_id="sdr-2", phone="212-555-0101")
        contact_of_loser = {"id": "contact-1", "prospect_id": loser["id"]}
        tables = make_tables(
            prospects=[survivor, loser],
            prospect_contacts=[contact_of_loser],
            profiles=[{"id": "sdr-1", "display_name": "First Rep"}, {"id": "sdr-2", "display_name": "Second Rep"}],
        )
        blocked_plan = make_merge_plan(
            survivor, [loser], blocker_reasons=["different SDRs own this company: P-900001 (sdr-1), P-900002 (sdr-2)"]
        )

        # When
        merged_tables, audit_rows = sut(tables, [blocked_plan], review_items=[], is_dry_run=False)

        # Then
        self.assertEqual(merged_tables, tables)
        self.assertEqual(audit_rows[0]["status"], "needs_review")
        self.assertEqual(
            audit_rows[0]["details"],
            "different SDRs own this company: P-900001 (First Rep), P-900002 (Second Rep)",
        )

    def test_run_merge_plans_audits_a_group_without_survivor_as_needs_review(self):
        # Given
        sut = self.make_sut()
        first_loser = make_prospect("P-900001", merged_into_id="id-9")
        second_loser = make_prospect("P-900002", merged_into_id="id-9")
        tables = make_tables(prospects=[first_loser, second_loser])
        plan_without_survivor = make_merge_plan(
            None, [first_loser, second_loser], blocker_reasons=["no row can survive"]
        )

        # When
        merged_tables, audit_rows = sut(tables, [plan_without_survivor], review_items=[], is_dry_run=False)

        # Then
        self.assertEqual(merged_tables, tables)
        self.assertEqual(
            [(audit_row["survivor_code"], audit_row["loser_code"], audit_row["status"]) for audit_row in audit_rows],
            [("", "P-900001", "needs_review"), ("", "P-900002", "needs_review")],
        )

    # Helpers

    def make_sut(self):
        return partial(run_merge_plans, merge_timestamp=MERGE_TIMESTAMP, make_id=fixed_id)


# Shared helpers

MERGE_TIMESTAMP = "2026-11-18T12:00:00+00:00"


def fixed_id():
    return "new-id"


def make_tables(**rows_by_table_name):
    tables = {table_name: [] for table_name in TABLE_NAMES}
    tables.update(rows_by_table_name)
    return tables


def make_merge_plan(survivor, losers, blocker_reasons=(), match_reason="website domain shop-a.com"):
    return {
        "identity_key": "shop-a.com",
        "survivor": survivor,
        "losers": losers,
        "match_reasons": {prospect["prospect_code"]: match_reason for prospect in [survivor, *losers] if prospect},
        "blocker_reasons": list(blocker_reasons),
    }


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
