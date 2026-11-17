import unittest

from dedup.identity import phone_identity_key, website_identity_key


class TestWebsiteIdentityKey(unittest.TestCase):

    def test_removes_https_www_and_trailing_slash(self):
        self.assertEqual(website_identity_key("https://www.cedartool.com/"), "cedartool.com")

    def test_two_spellings_of_the_same_website_give_the_same_key(self):
        cedar_key_from_import = website_identity_key("https://www.cedartool.com/")
        cedar_key_typed_by_hand = website_identity_key("cedartool.com")

        self.assertEqual(cedar_key_from_import, cedar_key_typed_by_hand)

    def test_upper_case_and_spaces_do_not_change_the_key(self):
        self.assertEqual(website_identity_key("  HTTPS://CedarTool.com "), "cedartool.com")

    def test_page_path_query_and_port_are_not_part_of_the_key(self):
        website_with_extras = "https://www.cedartool.com:443/contact?source=import"

        self.assertEqual(website_identity_key(website_with_extras), "cedartool.com")

    def test_a_subdomain_gives_the_root_domain(self):
        self.assertEqual(
            website_identity_key("https://waco.zenithstamping.com"), "zenithstamping.com"
        )

    def test_a_subdomain_of_a_generic_domain_has_no_key(self):
        self.assertIsNone(website_identity_key("https://mail.yahoo.com"))

    def test_a_generic_email_domain_does_not_identify_a_company(self):
        self.assertIsNone(website_identity_key("gmail.com"))
        self.assertIsNone(website_identity_key("https://www.yahoo.com/"))

    def test_an_empty_website_has_no_key(self):
        self.assertIsNone(website_identity_key(""))
        self.assertIsNone(website_identity_key("   "))

    def test_text_that_is_not_a_website_has_no_key(self):
        self.assertIsNone(website_identity_key("n/a"))


class TestPhoneIdentityKey(unittest.TestCase):

    def test_two_formats_of_the_same_phone_give_the_same_key(self):
        granite_phone_with_dots = phone_identity_key("814.555.0199")
        granite_phone_with_parentheses = phone_identity_key("(814) 555-0199")

        self.assertEqual(granite_phone_with_dots, "8145550199")
        self.assertEqual(granite_phone_with_parentheses, "8145550199")

    def test_the_us_country_code_is_not_part_of_the_key(self):
        self.assertEqual(phone_identity_key("+1 814-555-0199"), "8145550199")

    def test_an_empty_phone_has_no_key(self):
        self.assertIsNone(phone_identity_key(""))

    def test_a_phone_without_ten_digits_has_no_key(self):
        self.assertIsNone(phone_identity_key("555-0199"))
