"""Names shared by reading, processing and writing: the input tables and the audit file."""

TABLE_NAMES = [
    "profiles",
    "prospects",
    "prospect_aliases",
    "prospect_contacts",
    "sdr_follow_up_tasks",
    "power_dialer_call_logs",
    "email_activities",
    "prospect_contact_notes",
    "prospect_meetings",
]

# A company has at most 3 email slots (product rule).
EMAIL_FIELD_NAMES = ["email", "email_secondary", "email_tertiary"]

# Columns of output/merge_audit.csv, in order.
AUDIT_COLUMN_NAMES = ["request_id", "survivor_code", "loser_code", "dry_run", "status", "details"]
