import unittest

from dedup.blockers import find_conflicting_sdrs


class FindConflictingSdrsTests(unittest.TestCase):

    def test_find_conflicting_sdrs_delivers_no_blocker_on_rows_without_sdr(self):
        # Given
        sut = self.make_sut()
        first_row_without_sdr = make_prospect("P-900001")
        second_row_without_sdr = make_prospect("P-900002")

        # When / Then
        expect_no_blocker(self, sut, [first_row_without_sdr, second_row_without_sdr])

    def test_find_conflicting_sdrs_delivers_no_blocker_on_a_single_assigned_sdr(self):
        # Given
        sut = self.make_sut()
        row_with_sdr = make_prospect("P-900001", assigned_sdr_id="sdr-1")
        row_without_sdr = make_prospect("P-900002")

        # When / Then
        expect_no_blocker(self, sut, [row_with_sdr, row_without_sdr])

    def test_find_conflicting_sdrs_delivers_no_blocker_on_the_same_sdr_in_every_row(self):
        # Given
        sut = self.make_sut()
        first_row_of_sdr = make_prospect("P-900001", assigned_sdr_id="sdr-1")
        second_row_of_same_sdr = make_prospect("P-900002", assigned_sdr_id="sdr-1")

        # When / Then
        expect_no_blocker(self, sut, [first_row_of_sdr, second_row_of_same_sdr])

    def test_find_conflicting_sdrs_delivers_blocker_on_two_different_sdrs(self):
        # Given
        sut = self.make_sut()
        row_of_first_sdr = make_prospect("P-900001", assigned_sdr_id="sdr-1")
        row_of_second_sdr = make_prospect("P-900002", assigned_sdr_id="sdr-2")

        # When / Then
        expect_blocker(
            self,
            sut,
            [row_of_first_sdr, row_of_second_sdr],
            mentioning=["different SDRs", "P-900001 (sdr-1)", "P-900002 (sdr-2)"],
        )

    # Helpers

    def make_sut(self):
        return find_conflicting_sdrs


# Shared helpers

def expect_no_blocker(test_case, sut, prospects_in_group):
    test_case.assertIsNone(sut(prospects_in_group))


def expect_blocker(test_case, sut, prospects_in_group, mentioning):
    blocker_reason = sut(prospects_in_group)

    test_case.assertIsNotNone(blocker_reason)
    for expected_text in mentioning:
        test_case.assertIn(expected_text, blocker_reason)


def make_prospect(prospect_code, website="", assigned_sdr_id="", emails=()):
    email_slots = list(emails) + [""] * (3 - len(emails))
    return {
        "prospect_code": prospect_code,
        "website": website,
        "tusdr_assigned_user_id": assigned_sdr_id,
        "email": email_slots[0],
        "email_secondary": email_slots[1],
        "email_tertiary": email_slots[2],
    }
