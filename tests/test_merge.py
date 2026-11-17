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

    def test_move_child_rows_moves_loser_rows_of_every_child_table(self):
        # Given
        sut = self.make_sut()
        tables = make_tables(**{
            table_name: [make_child_row(LOSER_ID)] for table_name in CHILD_TABLE_NAMES
        })

        # When
        sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        for table_name in CHILD_TABLE_NAMES:
            self.assertEqual(tables[table_name][0]["prospect_id"], SURVIVOR_ID, table_name)

    def test_move_child_rows_delivers_no_counts_on_tables_without_loser_rows(self):
        # Given
        sut = self.make_sut()
        tables = make_tables(prospect_contacts=[make_child_row(SURVIVOR_ID)])

        # When
        moved_row_counts = sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        self.assertEqual(moved_row_counts, {})

    def test_move_child_rows_delivers_how_many_rows_moved_per_table(self):
        # Given
        sut = self.make_sut()
        tables = make_tables(
            prospect_contacts=[make_child_row(LOSER_ID), make_child_row(LOSER_ID)],
            sdr_follow_up_tasks=[make_child_row(LOSER_ID)],
            power_dialer_call_logs=[make_child_row(SURVIVOR_ID)],
        )

        # When
        moved_row_counts = sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        self.assertEqual(moved_row_counts, {"prospect_contacts": 2, "sdr_follow_up_tasks": 1})

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
