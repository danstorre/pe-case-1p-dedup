import unittest
from functools import partial

from dedup.audit import AUDIT_COLUMN_NAMES, build_audit_row


class BuildAuditRowTests(unittest.TestCase):

    def test_build_audit_row_delivers_the_survivor_and_loser_codes(self):
        # Given
        sut = self.make_sut()
        survivor = make_prospect("P-900001")
        loser = make_prospect("P-900002")

        # When
        audit_row = sut(survivor, loser, is_dry_run=False, status="merged", details="")

        # Then
        self.assertEqual(audit_row["survivor_code"], "P-900001")
        self.assertEqual(audit_row["loser_code"], "P-900002")

    def test_build_audit_row_delivers_dry_run_true_on_a_dry_run(self):
        # Given
        sut = self.make_sut()

        # When
        audit_row = sut(any_survivor(), any_loser(), is_dry_run=True, status="planned", details="")

        # Then
        self.assertEqual(audit_row["dry_run"], "true")

    def test_build_audit_row_delivers_dry_run_false_on_a_real_merge(self):
        # Given
        sut = self.make_sut()

        # When
        audit_row = sut(any_survivor(), any_loser(), is_dry_run=False, status="merged", details="")

        # Then
        self.assertEqual(audit_row["dry_run"], "false")

    def test_build_audit_row_delivers_the_status_and_details(self):
        # Given
        sut = self.make_sut()

        # When
        audit_row = sut(
            any_survivor(), any_loser(), is_dry_run=False, status="needs_review", details="different SDRs"
        )

        # Then
        self.assertEqual(audit_row["status"], "needs_review")
        self.assertEqual(audit_row["details"], "different SDRs")

    def test_build_audit_row_delivers_a_new_request_id_for_every_attempt(self):
        # Given
        sut = partial(build_audit_row, make_request_id=make_sequential_ids("request-1", "request-2"))

        # When
        first_audit_row = sut(any_survivor(), any_loser(), is_dry_run=False, status="merged", details="")
        second_audit_row = sut(any_survivor(), any_loser(), is_dry_run=False, status="merged", details="")

        # Then
        self.assertEqual(first_audit_row["request_id"], "request-1")
        self.assertEqual(second_audit_row["request_id"], "request-2")

    def test_build_audit_row_delivers_an_empty_survivor_code_when_there_is_no_survivor(self):
        # Given
        sut = self.make_sut()

        # When
        audit_row = sut(None, any_loser(), is_dry_run=False, status="needs_review", details="")

        # Then
        self.assertEqual(audit_row["survivor_code"], "")

    def test_build_audit_row_delivers_exactly_the_audit_columns_in_order(self):
        # Given
        sut = self.make_sut()

        # When
        audit_row = sut(any_survivor(), any_loser(), is_dry_run=False, status="merged", details="")

        # Then
        self.assertEqual(list(audit_row.keys()), AUDIT_COLUMN_NAMES)

    # Helpers

    def make_sut(self):
        return partial(build_audit_row, make_request_id=fixed_request_id)


# Shared helpers

def make_prospect(prospect_code):
    return {"prospect_code": prospect_code}


def fixed_request_id():
    return "request-1"


def any_survivor():
    return make_prospect("P-900001")


def any_loser():
    return make_prospect("P-900002")


def make_sequential_ids(*ids_in_order):
    remaining_ids = iter(ids_in_order)

    def next_id():
        return next(remaining_ids)

    return next_id
