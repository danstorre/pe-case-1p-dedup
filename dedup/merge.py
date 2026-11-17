"""The merge actions. They change the in-memory tables they receive, never the files in data/."""
import uuid

from dedup.tables import EMAIL_FIELD_NAMES

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

# Company data the survivor can take from a loser. Identity, pipeline and merge history
# (id, code, name, status, source, timestamps, merged_into_id, archived_at) never move.
FILLABLE_FIELD_NAMES = [
    "website",
    "phone",
    "phone_secondary",
    "city",
    "state",
    "employee_count",
    "tusdr_assigned_user_id",
]


def fill_empty_fields(survivor_prospect, loser_prospect):
    """Fill-only: copy a loser value only into an empty survivor field. Never overwrite.

    Returns the fields it filled, with their new value, for the audit trail.
    """
    filled_fields = {}
    for field_name in FILLABLE_FIELD_NAMES:
        loser_value = loser_prospect[field_name]
        survivor_field_is_empty = survivor_prospect[field_name] == ""
        if survivor_field_is_empty and loser_value != "":
            survivor_prospect[field_name] = loser_value
            filled_fields[field_name] = loser_value
    return filled_fields


def fill_empty_email_slots(survivor_prospect, loser_prospect):
    """Put each loser email the survivor does not have yet in its first free email slot.

    Returns the slots it filled, with their new email, for the audit trail.
    """
    filled_slots = {}
    survivor_emails = {
        survivor_prospect[slot_name].strip().lower()
        for slot_name in EMAIL_FIELD_NAMES
        if survivor_prospect[slot_name].strip()
    }
    for loser_email_field_name in EMAIL_FIELD_NAMES:
        loser_email = loser_prospect[loser_email_field_name].strip()
        if loser_email == "" or loser_email.lower() in survivor_emails:
            continue
        first_free_slot_name = next(
            (slot_name for slot_name in EMAIL_FIELD_NAMES if survivor_prospect[slot_name] == ""),
            None,
        )
        if first_free_slot_name is None:
            # The email blocker stops these groups before a merge. Never drop an email silently.
            raise ValueError(f"no free email slot for {loser_email}")
        survivor_prospect[first_free_slot_name] = loser_email
        survivor_emails.add(loser_email.lower())
        filled_slots[first_free_slot_name] = loser_email
    return filled_slots


def new_record_id():
    return str(uuid.uuid4())


def archive_loser(tables, loser_prospect, survivor_prospect, merge_timestamp, new_record_id=new_record_id):
    """Never delete: the loser stays in the file, points to the survivor and is hidden from SDRs."""
    loser_prospect["merged_into_id"] = survivor_prospect["id"]
    loser_prospect["archived_at"] = merge_timestamp
