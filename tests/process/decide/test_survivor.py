import unittest

from dedup.process.decide.survivor import choose_survivor


class ChooseSurvivorTests(unittest.TestCase):

    def test_choose_survivor_delivers_the_row_furthest_along_the_pipeline(self):
        # Given
        sut = self.make_sut()
        row_not_yet_contacted = make_prospect("P-900001", status="not_yet_contacted")
        row_with_intro_meeting = make_prospect("P-900002", status="intro_meeting")

        # When / Then
        self.expect(sut, [row_not_yet_contacted, row_with_intro_meeting], delivers_survivor="P-900002")

    def test_choose_survivor_delivers_the_row_with_an_assigned_sdr_on_equal_status(self):
        # Given
        sut = self.make_sut()
        row_without_sdr = make_prospect("P-900001", assigned_sdr_id="")
        row_with_sdr = make_prospect("P-900002", assigned_sdr_id=any_sdr_id())

        # When / Then
        self.expect(sut, [row_without_sdr, row_with_sdr], delivers_survivor="P-900002")

    def test_choose_survivor_delivers_the_oldest_row_on_equal_status_and_sdr(self):
        # Given
        sut = self.make_sut()
        newer_row = make_prospect("P-900001", created_at="2026-08-01T00:00:00+00:00")
        older_row = make_prospect("P-900002", created_at="2026-06-01T00:00:00+00:00")

        # When / Then
        self.expect(sut, [newer_row, older_row], delivers_survivor="P-900002")

    def test_choose_survivor_never_delivers_a_row_that_already_lost_a_merge(self):
        # Given
        sut = self.make_sut()
        row_that_lost_a_merge = make_prospect("P-900001", status="intro_meeting", merged_into_id="id-2")
        row_it_was_merged_into = make_prospect("P-900002", status="not_yet_contacted")

        # When / Then
        self.expect(sut, [row_that_lost_a_merge, row_it_was_merged_into], delivers_survivor="P-900002")

    def test_choose_survivor_delivers_no_survivor_when_every_row_already_lost_a_merge(self):
        # Given
        sut = self.make_sut()
        first_row_that_lost_a_merge = make_prospect("P-900001", merged_into_id="id-9")
        second_row_that_lost_a_merge = make_prospect("P-900002", merged_into_id="id-9")

        # When / Then
        self.expect(
            sut, [first_row_that_lost_a_merge, second_row_that_lost_a_merge], delivers_survivor=None
        )

    # Helpers

    def make_sut(self):
        return choose_survivor

    def expect(self, sut, prospects_in_group, delivers_survivor):
        survivor = sut(prospects_in_group)

        received_survivor = survivor["prospect_code"] if survivor else None
        self.assertEqual(received_survivor, delivers_survivor)


def make_prospect(
    prospect_code,
    status="not_yet_contacted",
    assigned_sdr_id="",
    created_at="2026-07-01T00:00:00+00:00",
    merged_into_id="",
):
    return {
        "prospect_code": prospect_code,
        "status": status,
        "tusdr_assigned_user_id": assigned_sdr_id,
        "created_at": created_at,
        "merged_into_id": merged_into_id,
    }


def any_sdr_id():
    return "sdr-1"
