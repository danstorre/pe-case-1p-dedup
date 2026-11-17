"""Checks that stop a merge because a person has to decide.

Each check takes the rows of one duplicate group and returns the reason as text, or None.
"""


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
