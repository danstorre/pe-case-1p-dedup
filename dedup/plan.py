"""Put the pieces together: decide what to merge, then run the merges on a copy of the tables."""
import copy

from dedup.audit import (
    MERGED,
    NEEDS_REVIEW,
    PLANNED,
    build_audit_row,
    describe_merge,
    replace_user_ids_with_names,
)
from dedup.blockers import find_blockers
from dedup.grouping import find_duplicate_groups
from dedup.ids import new_record_id
from dedup.merge import archive_loser, fill_empty_email_slots, fill_empty_fields, move_child_rows
from dedup.survivor import choose_survivor


def plan_merges(prospects):
    """Decide, without changing anything, the survivor and losers of every duplicate group
    and whether a person has to decide first.

    Returns (merge_plans, review_items).
    """
    duplicate_groups, review_items = find_duplicate_groups(prospects)
    merge_plans = []
    for duplicate_group in duplicate_groups:
        prospects_in_group = duplicate_group["prospects"]
        survivor = choose_survivor(prospects_in_group)
        blocker_reasons = find_blockers(prospects_in_group)
        if survivor is None:
            blocker_reasons.append("no row can survive: every row already lost a merge")
        merge_plans.append({
            "identity_key": duplicate_group["identity_key"],
            "survivor": survivor,
            "losers": [prospect for prospect in prospects_in_group if prospect is not survivor],
            "match_reasons": duplicate_group["match_reasons"],
            "blocker_reasons": blocker_reasons,
        })
    return merge_plans, review_items


def run_merge_plans(tables, merge_plans, review_items, is_dry_run, merge_timestamp, make_id=new_record_id):
    """Run the merges on a copy of the tables. The tables received are never changed.

    Returns (merged_tables, audit_rows).
    """
    merged_tables = copy.deepcopy(tables)
    merge_status = PLANNED if is_dry_run else MERGED
    prospects_by_id = {prospect["id"]: prospect for prospect in merged_tables["prospects"]}
    audit_rows = []
    for merge_plan in merge_plans:
        if merge_plan["blocker_reasons"]:
            reasons_for_a_person = replace_user_ids_with_names(
                "; ".join(merge_plan["blocker_reasons"]), tables["profiles"]
            )
            for loser in merge_plan["losers"]:
                audit_rows.append(build_audit_row(
                    merge_plan["survivor"], loser, is_dry_run, NEEDS_REVIEW, reasons_for_a_person, make_id
                ))
            continue
        survivor = prospects_by_id[merge_plan["survivor"]["id"]]
        for loser_in_plan in merge_plan["losers"]:
            loser = prospects_by_id[loser_in_plan["id"]]
            moved_row_counts = move_child_rows(merged_tables, loser["id"], survivor["id"])
            filled_fields = fill_empty_fields(survivor, loser)
            filled_fields.update(fill_empty_email_slots(survivor, loser))
            added_alias = archive_loser(merged_tables, loser, survivor, merge_timestamp, make_id)
            details = describe_merge(
                merge_plan["match_reasons"][loser["prospect_code"]], moved_row_counts, filled_fields, added_alias
            )
            audit_rows.append(build_audit_row(survivor, loser, is_dry_run, merge_status, details, make_id))
    return merged_tables, audit_rows
