import unittest

from dedup.identity import phone_identity_key, website_identity_key


class WebsiteIdentityKeyTests(unittest.TestCase):

    def test_website_identity_key_delivers_root_domain_on_url_with_scheme_www_and_trailing_slash(self):
        self.expect("https://www.shop-a.com/", delivers="shop-a.com")

    def test_website_identity_key_delivers_root_domain_on_bare_domain(self):
        self.expect("shop-a.com", delivers="shop-a.com")

    def test_website_identity_key_delivers_lowercase_root_domain_on_mixed_case_and_spaces(self):
        self.expect("  HTTPS://Shop-A.com ", delivers="shop-a.com")

    def test_website_identity_key_delivers_root_domain_on_url_with_port_path_and_query(self):
        self.expect("https://www.shop-a.com:443/contact?source=import", delivers="shop-a.com")

    def test_website_identity_key_delivers_root_domain_on_subdomain(self):
        self.expect("https://plant-1.shop-a.com", delivers="shop-a.com")

    def test_website_identity_key_delivers_no_key_on_generic_email_domain(self):
        self.expect("gmail.com", delivers=None)
        self.expect("https://www.yahoo.com/", delivers=None)

    def test_website_identity_key_delivers_no_key_on_subdomain_of_generic_domain(self):
        self.expect("https://mail.yahoo.com", delivers=None)

    def test_website_identity_key_delivers_no_key_on_empty_website(self):
        self.expect("", delivers=None)
        self.expect("   ", delivers=None)

    def test_website_identity_key_delivers_no_key_on_text_that_is_not_a_domain(self):
        self.expect("n/a", delivers=None)

    # Helpers

    def expect(self, website, delivers):
        self.assertEqual(website_identity_key(website), delivers, f"website: {website!r}")


class PhoneIdentityKeyTests(unittest.TestCase):

    def test_phone_identity_key_delivers_ten_digits_on_any_format(self):
        self.expect("212.555.0101", delivers="2125550101")
        self.expect("(212) 555-0101", delivers="2125550101")

    def test_phone_identity_key_delivers_ten_digits_on_number_with_us_country_code(self):
        self.expect("+1 212-555-0101", delivers="2125550101")

    def test_phone_identity_key_delivers_no_key_on_empty_phone(self):
        self.expect("", delivers=None)

    def test_phone_identity_key_delivers_no_key_on_number_without_ten_digits(self):
        self.expect("555-0101", delivers=None)

    # Helpers

    def expect(self, phone, delivers):
        self.assertEqual(phone_identity_key(phone), delivers, f"phone: {phone!r}")
