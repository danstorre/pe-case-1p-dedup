import unittest

from dedup.process.decide.blockers import (
    find_conflicting_sdrs,
    find_different_hosts,
    find_blockers,
    find_emails_that_do_not_fit,
)


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


class FindEmailsThatDoNotFitTests(unittest.TestCase):

    def test_find_emails_that_do_not_fit_delivers_no_blocker_on_three_different_emails(self):
        # Given
        sut = self.make_sut()
        row_with_two_emails = make_prospect("P-900001", emails=("a@shop-a.com", "b@shop-a.com"))
        row_with_one_email = make_prospect("P-900002", emails=("c@shop-a.com",))

        # When / Then
        expect_no_blocker(self, sut, [row_with_two_emails, row_with_one_email])

    def test_find_emails_that_do_not_fit_delivers_no_blocker_on_the_same_email_in_two_rows(self):
        # Given
        sut = self.make_sut()
        row_with_three_emails = make_prospect(
            "P-900001", emails=("a@shop-a.com", "b@shop-a.com", "c@shop-a.com")
        )
        row_repeating_one_email = make_prospect("P-900002", emails=(" A@Shop-A.com ",))

        # When / Then
        expect_no_blocker(self, sut, [row_with_three_emails, row_repeating_one_email])

    def test_find_emails_that_do_not_fit_delivers_blocker_on_four_different_emails(self):
        # Given
        sut = self.make_sut()
        row_with_three_emails = make_prospect(
            "P-900001", emails=("a@shop-a.com", "b@shop-a.com", "c@shop-a.com")
        )
        row_with_a_fourth_email = make_prospect("P-900002", emails=("d@shop-a.com",))

        # When / Then
        expect_blocker(
            self,
            sut,
            [row_with_three_emails, row_with_a_fourth_email],
            mentioning=["4 different emails", "3 email slots", "d@shop-a.com"],
        )

    # Helpers

    def make_sut(self):
        return find_emails_that_do_not_fit


class FindDifferentHostsTests(unittest.TestCase):

    def test_find_different_hosts_delivers_no_blocker_on_www_and_bare_host(self):
        # Given
        sut = self.make_sut()
        row_with_www = make_prospect("P-900001", website="https://www.shop-a.com")
        row_without_www = make_prospect("P-900002", website="shop-a.com")

        # When / Then
        expect_no_blocker(self, sut, [row_with_www, row_without_www])

    def test_find_different_hosts_delivers_no_blocker_on_a_row_without_website(self):
        # Given
        sut = self.make_sut()
        row_with_website = make_prospect("P-900001", website="https://shop-a.com")
        row_without_website = make_prospect("P-900002")

        # When / Then
        expect_no_blocker(self, sut, [row_with_website, row_without_website])

    def test_find_different_hosts_delivers_no_blocker_on_a_row_with_a_generic_website(self):
        # Given
        sut = self.make_sut()
        row_with_website = make_prospect("P-900001", website="https://shop-a.com")
        row_with_generic_website = make_prospect("P-900002", website="gmail.com")

        # When / Then
        expect_no_blocker(self, sut, [row_with_website, row_with_generic_website])

    def test_find_different_hosts_delivers_blocker_on_a_subdomain_and_the_root_domain(self):
        # Given
        sut = self.make_sut()
        row_of_a_plant = make_prospect("P-900001", website="https://plant-1.shop-a.com")
        row_of_the_main_site = make_prospect("P-900002", website="https://shop-a.com")

        # When / Then
        expect_blocker(
            self,
            sut,
            [row_of_a_plant, row_of_the_main_site],
            mentioning=["different hosts", "plant-1.shop-a.com", "shop-a.com"],
        )

    # Helpers

    def make_sut(self):
        return find_different_hosts


class FindBlockersTests(unittest.TestCase):

    def test_find_blockers_delivers_no_reasons_on_a_group_that_can_merge(self):
        # Given
        sut = self.make_sut()
        row_with_sdr = make_prospect("P-900001", website="https://shop-a.com", assigned_sdr_id="sdr-1")
        row_without_sdr = make_prospect("P-900002", website="shop-a.com")

        # When
        blocker_reasons = sut([row_with_sdr, row_without_sdr])

        # Then
        self.assertEqual(blocker_reasons, [])

    def test_find_blockers_delivers_every_reason_on_a_group_with_several_problems(self):
        # Given
        sut = self.make_sut()
        row_of_a_plant = make_prospect(
            "P-900001",
            website="https://plant-1.shop-a.com",
            assigned_sdr_id="sdr-1",
            emails=("a@shop-a.com", "b@shop-a.com", "c@shop-a.com"),
        )
        row_of_the_main_site = make_prospect(
            "P-900002",
            website="https://shop-a.com",
            assigned_sdr_id="sdr-2",
            emails=("d@shop-a.com",),
        )

        # When
        blocker_reasons = sut([row_of_a_plant, row_of_the_main_site])

        # Then
        self.assertEqual(len(blocker_reasons), 3)
        self.assertIn("different SDRs", blocker_reasons[0])
        self.assertIn("do not fit", blocker_reasons[1])
        self.assertIn("different hosts", blocker_reasons[2])

    # Helpers

    def make_sut(self):
        return find_blockers


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
