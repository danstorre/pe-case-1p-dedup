import unittest

from dedup.identity import phone_identity_key, website_host_name, website_identity_key


class WebsiteIdentityKeyTests(unittest.TestCase):

    def test_website_identity_key_delivers_root_domain_on_url_with_scheme_www_and_trailing_slash(self):
        # Given
        sut = self.make_sut()
        full_url = "https://www.shop-a.com/"

        # When
        received_key = sut(full_url)

        # Then
        self.assertEqual(received_key, "shop-a.com")

    def test_website_identity_key_delivers_root_domain_on_bare_domain(self):
        # Given
        sut = self.make_sut()
        bare_domain = "shop-a.com"

        # When
        received_key = sut(bare_domain)

        # Then
        self.assertEqual(received_key, "shop-a.com")

    def test_website_identity_key_delivers_lowercase_root_domain_on_mixed_case_and_spaces(self):
        # Given
        sut = self.make_sut()
        mixed_case_url_with_spaces = "  HTTPS://Shop-A.com "

        # When
        received_key = sut(mixed_case_url_with_spaces)

        # Then
        self.assertEqual(received_key, "shop-a.com")

    def test_website_identity_key_delivers_root_domain_on_url_with_port_path_and_query(self):
        # Given
        sut = self.make_sut()
        url_with_port_path_and_query = "https://www.shop-a.com:443/contact?source=import"

        # When
        received_key = sut(url_with_port_path_and_query)

        # Then
        self.assertEqual(received_key, "shop-a.com")

    def test_website_identity_key_delivers_root_domain_on_subdomain(self):
        # Given
        sut = self.make_sut()
        subdomain_url = "https://plant-1.shop-a.com"

        # When
        received_key = sut(subdomain_url)

        # Then
        self.assertEqual(received_key, "shop-a.com")

    def test_website_identity_key_delivers_no_key_on_generic_email_domain(self):
        # Given
        sut = self.make_sut()
        generic_email_domain = "gmail.com"

        # When
        received_key = sut(generic_email_domain)

        # Then
        self.assertIsNone(received_key)

    def test_website_identity_key_delivers_no_key_on_subdomain_of_generic_domain(self):
        # Given
        sut = self.make_sut()
        generic_subdomain_url = "https://mail.yahoo.com"

        # When
        received_key = sut(generic_subdomain_url)

        # Then
        self.assertIsNone(received_key)

    def test_website_identity_key_delivers_no_key_on_empty_website(self):
        # Given
        sut = self.make_sut()
        empty_website = ""

        # When
        received_key = sut(empty_website)

        # Then
        self.assertIsNone(received_key)

    def test_website_identity_key_delivers_no_key_on_blank_website(self):
        # Given
        sut = self.make_sut()
        blank_website = "   "

        # When
        received_key = sut(blank_website)

        # Then
        self.assertIsNone(received_key)

    def test_website_identity_key_delivers_no_key_on_text_that_is_not_a_domain(self):
        # Given
        sut = self.make_sut()
        text_that_is_not_a_domain = "n/a"

        # When
        received_key = sut(text_that_is_not_a_domain)

        # Then
        self.assertIsNone(received_key)

    # Helpers

    def make_sut(self):
        return website_identity_key


class WebsiteHostNameTests(unittest.TestCase):

    def test_website_host_name_delivers_host_without_www(self):
        # Given
        sut = self.make_sut()
        url_with_www = "https://www.shop-a.com/contact"

        # When
        received_host_name = sut(url_with_www)

        # Then
        self.assertEqual(received_host_name, "shop-a.com")

    def test_website_host_name_keeps_the_subdomain(self):
        # Given
        sut = self.make_sut()
        subdomain_url = "https://plant-1.shop-a.com"

        # When
        received_host_name = sut(subdomain_url)

        # Then
        self.assertEqual(received_host_name, "plant-1.shop-a.com")

    def test_website_host_name_delivers_no_host_on_empty_website(self):
        # Given
        sut = self.make_sut()
        empty_website = ""

        # When
        received_host_name = sut(empty_website)

        # Then
        self.assertIsNone(received_host_name)

    # Helpers

    def make_sut(self):
        return website_host_name


class PhoneIdentityKeyTests(unittest.TestCase):

    def test_phone_identity_key_delivers_ten_digits_on_phone_with_dots(self):
        # Given
        sut = self.make_sut()
        phone_with_dots = "212.555.0101"

        # When
        received_key = sut(phone_with_dots)

        # Then
        self.assertEqual(received_key, "2125550101")

    def test_phone_identity_key_delivers_ten_digits_on_phone_with_parentheses(self):
        # Given
        sut = self.make_sut()
        phone_with_parentheses = "(212) 555-0101"

        # When
        received_key = sut(phone_with_parentheses)

        # Then
        self.assertEqual(received_key, "2125550101")

    def test_phone_identity_key_delivers_ten_digits_on_phone_with_us_country_code(self):
        # Given
        sut = self.make_sut()
        phone_with_us_country_code = "+1 212-555-0101"

        # When
        received_key = sut(phone_with_us_country_code)

        # Then
        self.assertEqual(received_key, "2125550101")

    def test_phone_identity_key_delivers_no_key_on_empty_phone(self):
        # Given
        sut = self.make_sut()
        empty_phone = ""

        # When
        received_key = sut(empty_phone)

        # Then
        self.assertIsNone(received_key)

    def test_phone_identity_key_delivers_no_key_on_phone_without_ten_digits(self):
        # Given
        sut = self.make_sut()
        phone_without_area_code = "555-0101"

        # When
        received_key = sut(phone_without_area_code)

        # Then
        self.assertIsNone(received_key)

    # Helpers

    def make_sut(self):
        return phone_identity_key
