"""Find the groups of companies that share an identity."""
from dedup.identity import phone_identity_key, website_identity_key


def find_duplicate_groups(prospects):
    """Group the companies that share an identity.

    Returns (duplicate_groups, review_items). A duplicate group has two or more companies.
    """
    prospects_by_identity_key = {}
    match_reason_by_prospect_code = {}
    prospects_without_website_key = []

    # First: companies with a usable website are grouped by root domain.
    for prospect in prospects:
        website_key = website_identity_key(prospect["website"])
        if website_key is None:
            prospects_without_website_key.append(prospect)
            continue
        prospects_by_identity_key.setdefault(website_key, []).append(prospect)
        match_reason_by_prospect_code[prospect["prospect_code"]] = f"website domain {website_key}"

    # Index: main phone -> website domains that use it.
    website_keys_by_phone_key = {}
    for website_key, prospects_with_website in prospects_by_identity_key.items():
        for prospect in prospects_with_website:
            phone_key = phone_identity_key(prospect["phone"])
            if phone_key is not None:
                website_keys_by_phone_key.setdefault(phone_key, set()).add(website_key)

    # Then: companies without a usable website are identified by main phone.
    review_items = []
    for prospect in prospects_without_website_key:
        phone_key = phone_identity_key(prospect["phone"])
        if phone_key is None:
            review_items.append({
                "prospect_code": prospect["prospect_code"],
                "reason": "no website and no main phone: cannot tell if it is a duplicate",
            })
            continue
        website_keys_with_this_phone = sorted(website_keys_by_phone_key.get(phone_key, []))
        if len(website_keys_with_this_phone) > 1:
            review_items.append({
                "prospect_code": prospect["prospect_code"],
                "reason": f"no website; main phone {phone_key} is used by several companies: "
                          + ", ".join(website_keys_with_this_phone),
            })
            continue
        if len(website_keys_with_this_phone) == 1:
            identity_key = website_keys_with_this_phone[0]
            match_reason = f"no website; main phone {phone_key} belongs to {identity_key}"
        else:
            identity_key = f"phone {phone_key}"
            match_reason = f"no website; main phone {phone_key}"
        prospects_by_identity_key.setdefault(identity_key, []).append(prospect)
        match_reason_by_prospect_code[prospect["prospect_code"]] = match_reason

    duplicate_groups = [
        {
            "identity_key": identity_key,
            "prospects": prospects_in_group,
            "match_reasons": {
                prospect["prospect_code"]: match_reason_by_prospect_code[prospect["prospect_code"]]
                for prospect in prospects_in_group
            },
        }
        for identity_key, prospects_in_group in prospects_by_identity_key.items()
        if len(prospects_in_group) >= 2
    ]
    return duplicate_groups, review_items
