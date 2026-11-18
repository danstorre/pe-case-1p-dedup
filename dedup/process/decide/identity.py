"""Business rule: a company is identified by its root website domain, or else its main phone."""
from urllib.parse import urlsplit

# Domains anyone can have an address on. They never identify a company.
GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com",
}


def website_host_name(website):
    """The host of a website, lowercase and without "www.", or None if there is none."""
    website_text = website.strip()
    if "://" not in website_text:
        website_text = "//" + website_text      # urlsplit only finds the host after "//"
    host_name = urlsplit(website_text).hostname or ""
    if host_name.startswith("www."):
        host_name = host_name[len("www."):]
    return host_name or None


def website_identity_key(website):
    """Turn a website as imported into the key that identifies the company.

    Returns None when the website cannot identify a company.
    """
    host_name = website_host_name(website)
    if host_name is None:
        return None
    host_labels = host_name.split(".")           # "plant-1.shop-a.com" -> 3 labels
    host_looks_like_a_domain = len(host_labels) >= 2
    if not host_looks_like_a_domain:
        return None
    root_domain = ".".join(host_labels[-2:])     # keep the last two: "shop-a.com"
    if root_domain in GENERIC_DOMAINS:
        return None
    return root_domain


def phone_identity_key(phone):
    """Turn a phone as imported into its ten digits, or None if it is not a full US number."""
    phone_digits = "".join(character for character in phone if character.isdigit())
    has_us_country_code = len(phone_digits) == 11 and phone_digits.startswith("1")
    if has_us_country_code:
        phone_digits = phone_digits[1:]
    if len(phone_digits) != 10:
        return None
    return phone_digits
