"""The audit trail: one row per merge attempt, so every decision can be traced."""
from dedup.ids import new_record_id

AUDIT_COLUMN_NAMES = ["request_id", "survivor_code", "loser_code", "dry_run", "status", "details"]

# Status of a merge attempt.
MERGED = "merged"
PLANNED = "planned"            # dry run: it would have merged
NEEDS_REVIEW = "needs_review"  # stopped: a person has to decide


def build_audit_row(
    survivor_prospect, loser_prospect, is_dry_run, status, details, make_request_id=new_record_id
):
    """One audit row per merge attempt, blocked attempts included. Survivor can be None."""
    return {
        "request_id": make_request_id(),
        "survivor_code": survivor_prospect["prospect_code"] if survivor_prospect else "",
        "loser_code": loser_prospect["prospect_code"],
        "dry_run": "true" if is_dry_run else "false",
        "status": status,
        "details": details,
    }
