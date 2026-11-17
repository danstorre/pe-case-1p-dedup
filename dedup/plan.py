"""Put the pieces together: decide what to merge, then run the merges on a copy of the tables."""
from dedup.blockers import find_blockers
from dedup.grouping import find_duplicate_groups
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
        merge_plans.append({
            "identity_key": duplicate_group["identity_key"],
            "survivor": survivor,
            "losers": [prospect for prospect in prospects_in_group if prospect is not survivor],
            "match_reasons": duplicate_group["match_reasons"],
            "blocker_reasons": find_blockers(prospects_in_group),
        })
    return merge_plans, review_items
