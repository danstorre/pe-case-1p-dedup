"""Checks that stop a merge because a person has to decide.

Each check takes the rows of one duplicate group and returns the reason as text, or None.
"""
from dedup.process.decide.identity import website_host_name, website_identity_key
from dedup.schema import EMAIL_FIELD_NAMES


def find_conflicting_sdrs(prospects_in_group):
    """Two different SDRs own rows of the same company: who keeps it is a business decision."""
    rows_with_assigned_sdr = [
        prospect for prospect in prospects_in_group if prospect["tusdr_assigned_user_id"]
    ]
    assigned_sdr_ids = {prospect["tusdr_assigned_user_id"] for prospect in rows_with_assigned_sdr}
    if len(assigned_sdr_ids) <= 1:
        return None
    owner_of_each_row = ", ".join(
        f"{prospect['prospect_code']} ({prospect['tusdr_assigned_user_id']})"
        for prospect in rows_with_assigned_sdr
    )
    return f"different SDRs own this company: {owner_of_each_row}"



def find_emails_that_do_not_fit(prospects_in_group):
    """A company has 3 email slots. Dropping an extra email is a decision for a person."""
    different_emails = []
    for prospect in prospects_in_group:
        for email_field_name in EMAIL_FIELD_NAMES:
            email = prospect[email_field_name].strip().lower()
            if email and email not in different_emails:
                different_emails.append(email)
    if len(different_emails) <= len(EMAIL_FIELD_NAMES):
        return None
    return (
        f"{len(different_emails)} different emails do not fit in "
        f"{len(EMAIL_FIELD_NAMES)} email slots: {', '.join(different_emails)}"
    )


def find_different_hosts(prospects_in_group):
    """Same root domain but different hosts (e.g. a subdomain) can be separate plants or divisions."""
    different_host_names = sorted({
        website_host_name(prospect["website"])
        for prospect in prospects_in_group
        if website_identity_key(prospect["website"]) is not None
    })
    if len(different_host_names) <= 1:
        return None
    return (
        "rows use different hosts of the same domain, they may be separate sites: "
        + ", ".join(different_host_names)
    )


BLOCKER_CHECKS = [
    find_conflicting_sdrs,
    find_emails_that_do_not_fit,
    find_different_hosts,
]


def find_blockers(prospects_in_group):
    """Run every check. An empty list means the group can be merged without asking anyone."""
    blocker_reasons = []
    for blocker_check in BLOCKER_CHECKS:
        blocker_reason = blocker_check(prospects_in_group)
        if blocker_reason is not None:
            blocker_reasons.append(blocker_reason)
    return blocker_reasons
