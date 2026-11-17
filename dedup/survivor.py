"""Choose which row of a duplicate group keeps the company. The README leaves this rule to us."""

PIPELINE_STATUS_ORDER = [
    "not_yet_contacted",
    "contacted",
    "intro_meeting",
    "proposal_review_meeting",
    "closed_won",
    "closed_lost",
]


def choose_survivor(prospects_in_group):
    """The survivor is the row furthest along the pipeline, then the one with an assigned SDR,
    then the oldest one. A row that already lost a merge can never survive."""
    candidate_prospects = [
        prospect for prospect in prospects_in_group if not prospect["merged_into_id"]
    ]

    def survivor_ranking(prospect):
        pipeline_position = PIPELINE_STATUS_ORDER.index(prospect["status"])
        has_no_assigned_sdr = prospect["tusdr_assigned_user_id"] == ""
        return (-pipeline_position, has_no_assigned_sdr, prospect["created_at"])

    return min(candidate_prospects, key=survivor_ranking)
