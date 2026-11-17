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
    """The survivor is the row furthest along the pipeline."""

    def survivor_ranking(prospect):
        pipeline_position = PIPELINE_STATUS_ORDER.index(prospect["status"])
        return -pipeline_position

    return min(prospects_in_group, key=survivor_ranking)
