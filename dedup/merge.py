"""The merge actions. They change the in-memory tables they receive, never the files in data/."""

# Every table whose rows hang off a company through prospect_id.
CHILD_TABLE_NAMES = [
    "prospect_aliases",
    "prospect_contacts",
    "sdr_follow_up_tasks",
    "power_dialer_call_logs",
    "email_activities",
    "prospect_contact_notes",
    "prospect_meetings",
]


def move_child_rows(tables, loser_prospect_id, survivor_prospect_id):
    """Point every row that hangs off the loser to the survivor: history moves too, not only pending work.

    Returns how many rows moved, per table, for the audit trail.
    """
    moved_row_counts = {}
    for child_table_name in CHILD_TABLE_NAMES:
        for child_row in tables[child_table_name]:
            if child_row["prospect_id"] == loser_prospect_id:
                child_row["prospect_id"] = survivor_prospect_id
                moved_row_counts[child_table_name] = moved_row_counts.get(child_table_name, 0) + 1
    return moved_row_counts


def fill_empty_fields(survivor_prospect, loser_prospect):
    """Fill-only: copy a loser value only into an empty survivor field. Never overwrite."""
    for field_name, loser_value in loser_prospect.items():
        survivor_field_is_empty = survivor_prospect[field_name] == ""
        if survivor_field_is_empty and loser_value != "":
            survivor_prospect[field_name] = loser_value
