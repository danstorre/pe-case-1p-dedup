import unittest

from dedup.merge import move_child_rows

SURVIVOR_ID = "survivor-id"
LOSER_ID = "loser-id"
OTHER_COMPANY_ID = "other-company-id"


class MoveChildRowsTests(unittest.TestCase):

    def test_move_child_rows_moves_nothing_on_tables_without_loser_rows(self):
        # Given
        sut = self.make_sut()
        contact_of_survivor = make_child_row(SURVIVOR_ID)
        tables = make_tables(prospect_contacts=[contact_of_survivor])

        # When
        sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        self.assertEqual(contact_of_survivor["prospect_id"], SURVIVOR_ID)

    def test_move_child_rows_moves_a_loser_contact_to_the_survivor(self):
        # Given
        sut = self.make_sut()
        contact_of_loser = make_child_row(LOSER_ID)
        tables = make_tables(prospect_contacts=[contact_of_loser])

        # When
        sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        self.assertEqual(contact_of_loser["prospect_id"], SURVIVOR_ID)

    # Helpers

    def make_sut(self):
        return move_child_rows


CHILD_TABLE_NAMES = [
    "prospect_aliases",
    "prospect_contacts",
    "sdr_follow_up_tasks",
    "power_dialer_call_logs",
    "email_activities",
    "prospect_contact_notes",
    "prospect_meetings",
]


def make_tables(**rows_by_table_name):
    tables = {table_name: [] for table_name in CHILD_TABLE_NAMES}
    tables.update(rows_by_table_name)
    return tables


def make_child_row(prospect_id, **other_fields):
    return {"prospect_id": prospect_id, **other_fields}
