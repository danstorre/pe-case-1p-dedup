import unittest

from dedup.merge import fill_empty_email_slots, fill_empty_fields, move_child_rows

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

    def test_move_child_rows_keeps_pending_tasks_do_not_call_flags_and_booked_meetings(self):
        # Given
        sut = self.make_sut()
        pending_task = make_child_row(LOSER_ID, status="pending", due_at="2026-10-31T00:00:00+00:00")
        do_not_call_contact = make_child_row(LOSER_ID, do_not_call="true", lead_status="do_not_contact")
        booked_meeting = make_child_row(LOSER_ID, status="scheduled")
        tables = make_tables(
            sdr_follow_up_tasks=[pending_task],
            prospect_contacts=[do_not_call_contact],
            prospect_meetings=[booked_meeting],
        )

        # When
        sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        self.assertEqual(
            pending_task,
            {"prospect_id": SURVIVOR_ID, "status": "pending", "due_at": "2026-10-31T00:00:00+00:00"},
        )
        self.assertEqual(
            do_not_call_contact,
            {"prospect_id": SURVIVOR_ID, "do_not_call": "true", "lead_status": "do_not_contact"},
        )
        self.assertEqual(booked_meeting, {"prospect_id": SURVIVOR_ID, "status": "scheduled"})

    def test_move_child_rows_leaves_rows_of_other_companies_untouched(self):
        # Given
        sut = self.make_sut()
        contact_of_other_company = make_child_row(OTHER_COMPANY_ID)
        tables = make_tables(prospect_contacts=[contact_of_other_company, make_child_row(LOSER_ID)])

        # When
        sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        self.assertEqual(contact_of_other_company["prospect_id"], OTHER_COMPANY_ID)

    def test_move_child_rows_keeps_the_number_of_rows_in_every_table(self):
        # Given
        sut = self.make_sut()
        tables = make_tables(**{
            table_name: [make_child_row(LOSER_ID), make_child_row(OTHER_COMPANY_ID)]
            for table_name in CHILD_TABLE_NAMES
        })

        # When
        sut(tables, LOSER_ID, SURVIVOR_ID)

        # Then
        for table_name in CHILD_TABLE_NAMES:
            self.assertEqual(len(tables[table_name]), 2, table_name)

    # Helpers

    def make_sut(self):
        return move_child_rows

class FillEmptyFieldsTests(unittest.TestCase):

    def test_fill_empty_fields_fills_an_empty_survivor_field_with_the_loser_value(self):
        # Given
        sut = self.make_sut()
        survivor_without_phone = make_prospect(phone="")
        loser_with_phone = make_prospect(phone="212-555-0101")

        # When
        sut(survivor_without_phone, loser_with_phone)

        # Then
        self.assertEqual(survivor_without_phone["phone"], "212-555-0101")

    def test_fill_empty_fields_never_overwrites_a_field_the_survivor_already_has(self):
        # Given
        sut = self.make_sut()
        survivor_with_city = make_prospect(city="Springfield")
        loser_with_another_city = make_prospect(city="Shelbyville")

        # When
        sut(survivor_with_city, loser_with_another_city)

        # Then
        self.assertEqual(survivor_with_city["city"], "Springfield")

    def test_fill_empty_fields_never_copies_the_loser_merge_history(self):
        # Given
        sut = self.make_sut()
        survivor_never_merged = make_prospect(merged_into_id="", archived_at="")
        loser_that_lost_an_earlier_merge = make_prospect(
            merged_into_id="survivor-id", archived_at="2026-09-01T00:00:00+00:00"
        )

        # When
        sut(survivor_never_merged, loser_that_lost_an_earlier_merge)

        # Then
        self.assertEqual(survivor_never_merged["merged_into_id"], "")
        self.assertEqual(survivor_never_merged["archived_at"], "")

    def test_fill_empty_fields_delivers_nothing_when_nothing_was_filled(self):
        # Given
        sut = self.make_sut()
        survivor_with_phone = make_prospect(phone="212-555-0101")
        loser_without_data = make_prospect()

        # When
        filled_fields = sut(survivor_with_phone, loser_without_data)

        # Then
        self.assertEqual(filled_fields, {})

    def test_fill_empty_fields_delivers_the_fields_it_filled_with_their_new_value(self):
        # Given
        sut = self.make_sut()
        survivor_without_phone_or_state = make_prospect(phone="", state="", city="Springfield")
        loser_with_phone_state_and_city = make_prospect(
            phone="212-555-0101", state="Ohio", city="Shelbyville"
        )

        # When
        filled_fields = sut(survivor_without_phone_or_state, loser_with_phone_state_and_city)

        # Then
        self.assertEqual(filled_fields, {"phone": "212-555-0101", "state": "Ohio"})

    # Helpers

    def make_sut(self):
        return fill_empty_fields


class FillEmptyEmailSlotsTests(unittest.TestCase):

    def test_fill_empty_email_slots_puts_a_loser_email_in_the_first_free_slot(self):
        # Given
        sut = self.make_sut()
        survivor_with_one_email = make_prospect(email="info@shop-a.com")
        loser_with_another_email = make_prospect(email="sales@shop-a.com")

        # When
        sut(survivor_with_one_email, loser_with_another_email)

        # Then
        self.assertEqual(survivor_with_one_email["email"], "info@shop-a.com")
        self.assertEqual(survivor_with_one_email["email_secondary"], "sales@shop-a.com")
        self.assertEqual(survivor_with_one_email["email_tertiary"], "")

    # Helpers

    def make_sut(self):
        return fill_empty_email_slots



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


PROSPECT_FIELD_NAMES = [
    "id", "prospect_code", "shop_name", "website", "phone", "phone_secondary",
    "email", "email_secondary", "email_tertiary", "city", "state", "employee_count",
    "status", "tusdr_assigned_user_id", "record_source", "created_at", "updated_at",
    "merged_into_id", "archived_at",
]


def make_prospect(**fields):
    prospect = {field_name: "" for field_name in PROSPECT_FIELD_NAMES}
    prospect.update(fields)
    return prospect
