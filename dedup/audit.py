"""The audit trail: one row per merge attempt, so every decision can be traced."""
from dedup.ids import new_record_id


def build_audit_row(survivor_prospect, loser_prospect, is_dry_run, status, details, make_request_id=new_record_id):
    return {
        "survivor_code": survivor_prospect["prospect_code"],
        "loser_code": loser_prospect["prospect_code"],
    }
