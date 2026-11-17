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


def describe_merge(match_reason, moved_row_counts, filled_fields, added_alias):
    """The details text of an audit row: why the rows matched and what the merge changed."""
    detail_parts = [match_reason]
    if moved_row_counts:
        detail_parts.append("moved " + ", ".join(
            f"{moved_row_count} {table_name}" for table_name, moved_row_count in moved_row_counts.items()
        ))
    if filled_fields:
        detail_parts.append("filled " + ", ".join(
            f"{field_name}={filled_value}" for field_name, filled_value in filled_fields.items()
        ))
    if added_alias:
        detail_parts.append(f"added alias '{added_alias}'")
    return "; ".join(detail_parts)


def replace_user_ids_with_names(text, profiles):
    """Audit details are read by people: show the person's name instead of a user id."""
    readable_text = text
    for profile in profiles:
        readable_text = readable_text.replace(profile["id"], profile["display_name"])
    return readable_text
