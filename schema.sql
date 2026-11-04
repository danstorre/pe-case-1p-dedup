-- IJOS 1P Prospect Database - simplified schema for the Product Engineer case.
-- Mirrors the shape of the real system (names and semantics), trimmed to what the case needs.
-- PostgreSQL 14+.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Internal users (SDRs, BDMs, admins). No emails on purpose.
CREATE TABLE profiles (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name  text NOT NULL,
  role          text NOT NULL CHECK (role IN ('sdr','bdm','lead','admin')),
  is_active     boolean NOT NULL DEFAULT true
);

-- A company we prospect. One row per company. prospect_code is the human id (P-000123).
CREATE TABLE prospects (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_code           text NOT NULL UNIQUE,
  shop_name               text NOT NULL,
  website                 text,
  phone                   text,
  phone_secondary         text,
  email                   text,
  email_secondary         text,
  email_tertiary          text,
  address                 text,
  city                    text,
  state                   text,
  country                 text NOT NULL DEFAULT 'United States',
  employee_count          integer,
  status                  text NOT NULL DEFAULT 'not_yet_contacted'
                          CHECK (status IN ('not_yet_contacted','contacted','intro_meeting','proposal_review_meeting','closed_won','closed_lost')),
  tusdr_assigned_user_id  uuid REFERENCES profiles(id),
  bdm_assigned_user_id    uuid REFERENCES profiles(id),
  record_source           text,
  -- identity / lifecycle
  merged_into_id          uuid REFERENCES prospects(id),   -- set when this row lost a merge
  archived_at             timestamptz,                     -- set when hidden from the UI
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

-- Alternate names a company is known by. Search must find the company by any alias.
CREATE TABLE prospect_aliases (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id   uuid NOT NULL REFERENCES prospects(id),
  alias         text NOT NULL,
  kind          text NOT NULL DEFAULT 'manual',  -- manual | historical_merge | import
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX prospect_aliases_unique ON prospect_aliases (prospect_id, lower(alias));

-- People at the company.
CREATE TABLE prospect_contacts (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id   uuid NOT NULL REFERENCES prospects(id),
  full_name     text NOT NULL,
  title         text,
  email         text,
  mobile        text,
  lead_status   text CHECK (lead_status IN ('new','attempted_no_answer','meeting_booked','unqualified','do_not_contact')),
  do_not_call   boolean NOT NULL DEFAULT false,
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- Follow-up tasks an SDR owes a company/contact. When status = done the task leaves the SDR ledger.
CREATE TABLE sdr_follow_up_tasks (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id       uuid NOT NULL REFERENCES prospects(id),
  contact_id        uuid REFERENCES prospect_contacts(id),
  assignee_user_id  uuid NOT NULL REFERENCES profiles(id),
  task_type         text NOT NULL CHECK (task_type IN ('send_email','schedule_callback','note')),
  status            text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','done','cancelled')),
  note              text,
  due_at            timestamptz,
  completed_at      timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now()
);

-- Calls made from the power dialer.
CREATE TABLE power_dialer_call_logs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id   uuid NOT NULL REFERENCES prospects(id),
  contact_id    uuid REFERENCES prospect_contacts(id),
  user_id       uuid NOT NULL REFERENCES profiles(id),
  number_dialed text,
  outcome       text NOT NULL CHECK (outcome IN ('reached','voicemail','not_reached','bad_number')),
  duration_sec  integer NOT NULL DEFAULT 0,
  called_at     timestamptz NOT NULL DEFAULT now()
);

-- Outbound emails sent by SDRs (matched to a company by contact email or company domain).
CREATE TABLE email_activities (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id   uuid NOT NULL REFERENCES prospects(id),
  contact_id    uuid REFERENCES prospect_contacts(id),
  user_id       uuid NOT NULL REFERENCES profiles(id),
  to_address    text NOT NULL,
  subject       text,
  sent_at       timestamptz NOT NULL DEFAULT now()
);

-- Free-text notes on a contact.
CREATE TABLE prospect_contact_notes (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id   uuid NOT NULL REFERENCES prospects(id),
  contact_id    uuid REFERENCES prospect_contacts(id),
  author_user_id uuid NOT NULL REFERENCES profiles(id),
  body          text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- Meetings booked with a company.
CREATE TABLE prospect_meetings (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_id   uuid NOT NULL REFERENCES prospects(id),
  contact_id    uuid REFERENCES prospect_contacts(id),
  booked_by     uuid NOT NULL REFERENCES profiles(id),
  scheduled_at  timestamptz NOT NULL,
  status        text NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','done','no_show','cancelled'))
);

-- Audit trail for merges. Every merge must leave a row here.
CREATE TABLE prospect_merge_audit (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id        text NOT NULL,
  survivor_id       uuid NOT NULL REFERENCES prospects(id),
  loser_id          uuid NOT NULL REFERENCES prospects(id),
  dry_run           boolean NOT NULL,
  status            text NOT NULL,          -- planned | merged | requires_human_decision | error
  details           jsonb NOT NULL DEFAULT '{}'::jsonb,
  performed_by      uuid REFERENCES profiles(id),
  performed_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON prospects (lower(website));
CREATE INDEX ON prospects (phone);
CREATE INDEX ON prospects (merged_into_id);
CREATE INDEX ON prospect_contacts (prospect_id);
CREATE INDEX ON sdr_follow_up_tasks (prospect_id, status);
CREATE INDEX ON power_dialer_call_logs (prospect_id);
CREATE INDEX ON email_activities (prospect_id);

COMMIT;
