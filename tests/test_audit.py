import unittest
from functools import partial

from dedup.audit import build_audit_row


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

    # Helpers

    def make_sut(self):
        return partial(build_audit_row, make_request_id=fixed_request_id)


# Shared helpers

def make_prospect(prospect_code):
    return {"prospect_code": prospect_code}


def fixed_request_id():
    return "request-1"
