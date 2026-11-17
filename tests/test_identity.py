import unittest

from dedup.identity import phone_identity_key, website_identity_key


class TestWebsiteIdentityKey(unittest.TestCase):

    def test_scheme_www_and_trailing_slash_are_removed(self):
        self.assertEqual(website_identity_key("https://www.shop-a.com/"), "shop-a.com")

    def test_a_website_with_and_without_scheme_gives_the_same_key(self):
        key_with_scheme = website_identity_key("https://www.shop-a.com/")
        key_without_scheme = website_identity_key("shop-a.com")

        self.assertEqual(key_with_scheme, key_without_scheme)

    def test_upper_case_and_surrounding_spaces_are_ignored(self):
        self.assertEqual(website_identity_key("  HTTPS://Shop-A.com "), "shop-a.com")

    def test_port_path_and_query_are_ignored(self):
        website_with_port_path_and_query = "https://www.shop-a.com:443/contact?source=import"

        self.assertEqual(website_identity_key(website_with_port_path_and_query), "shop-a.com")

    def test_a_subdomain_gives_its_root_domain(self):
        self.assertEqual(website_identity_key("https://plant-1.shop-a.com"), "shop-a.com")

    def test_a_subdomain_of_a_generic_domain_gives_no_key(self):
        self.assertIsNone(website_identity_key("https://mail.yahoo.com"))

    def test_a_generic_email_domain_gives_no_key(self):
        self.assertIsNone(website_identity_key("gmail.com"))
        self.assertIsNone(website_identity_key("https://www.yahoo.com/"))

    def test_an_empty_website_gives_no_key(self):
        self.assertIsNone(website_identity_key(""))
        self.assertIsNone(website_identity_key("   "))

    def test_text_that_is_not_a_domain_gives_no_key(self):
        self.assertIsNone(website_identity_key("n/a"))


class TestPhoneIdentityKey(unittest.TestCase):

    def test_different_formats_of_one_phone_give_the_same_ten_digits(self):
        phone_with_dots = phone_identity_key("212.555.0101")
        phone_with_parentheses = phone_identity_key("(212) 555-0101")

        self.assertEqual(phone_with_dots, "2125550101")
        self.assertEqual(phone_with_parentheses, "2125550101")

    def test_the_us_country_code_is_dropped(self):
        self.assertEqual(phone_identity_key("+1 212-555-0101"), "2125550101")

    def test_an_empty_phone_gives_no_key(self):
        self.assertIsNone(phone_identity_key(""))

    def test_a_phone_without_ten_digits_gives_no_key(self):
        self.assertIsNone(phone_identity_key("555-0101"))
