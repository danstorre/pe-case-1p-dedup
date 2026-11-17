"""The merge actions. They change the in-memory tables they receive, never the files in data/."""


def move_child_rows(tables, loser_prospect_id, survivor_prospect_id):
    """Point every row that hangs off the loser to the survivor."""
    for child_row in tables["prospect_contacts"]:
        if child_row["prospect_id"] == loser_prospect_id:
            child_row["prospect_id"] = survivor_prospect_id
