# Data model

Nine CSV files in `data/`. They mirror the tables of our real system (same names, same
meaning), trimmed to what this case needs. All ids are UUIDs. Empty cell = NULL. Timestamps
are ISO-8601 UTC.

## profiles.csv - internal users

| column | notes |
|---|---|
| id | user id |
| display_name | |
| role | sdr, bdm, lead, admin |

## prospects.csv - companies (one row per company)

| column | notes |
|---|---|
| id | company id, referenced by every other file as `prospect_id` |
| prospect_code | human id, `P-000123`, unique |
| shop_name | company name as imported |
| website | as imported: may be missing, may have https / www / trailing slash |
| phone, phone_secondary | as imported, formats vary |
| email, email_secondary, email_tertiary | max 3 email slots per company (product rule) |
| city, state | |
| employee_count | may be missing |
| status | pipeline: not_yet_contacted, contacted, intro_meeting, proposal_review_meeting, closed_won, closed_lost |
| tusdr_assigned_user_id | SDR who owns the company (profiles.id), may be empty |
| record_source | which import created the row |
| created_at, updated_at | |
| merged_into_id | set when this row LOST a merge; points to the surviving prospects.id |
| archived_at | set when the row is hidden from SDRs. A merged row should be archived; some are not |

## prospect_aliases.csv - alternate names

| column | notes |
|---|---|
| id | |
| prospect_id | company this alias belongs to |
| alias | a name the company is also known by; search must find the company by it |
| kind | manual, historical_merge, import |

## prospect_contacts.csv - people at the company

| column | notes |
|---|---|
| id | |
| prospect_id | |
| full_name, title, email, mobile | |
| lead_status | new, attempted_no_answer, meeting_booked, unqualified, do_not_contact |
| do_not_call | true = legal/compliance flag, must never be lost |

## sdr_follow_up_tasks.csv - work an SDR owes a company

| column | notes |
|---|---|
| id | |
| prospect_id, contact_id | contact may be empty |
| assignee_user_id | SDR who owns the task |
| task_type | send_email, schedule_callback, note |
| status | pending, done, cancelled. Pending tasks make the company visible to the SDR |
| note | |
| due_at, completed_at, created_at | |

## power_dialer_call_logs.csv - calls

| column | notes |
|---|---|
| id, prospect_id, contact_id, user_id | |
| number_dialed | |
| outcome | reached, voicemail, not_reached, bad_number |
| duration_sec, called_at | |

## email_activities.csv - outbound emails

| column | notes |
|---|---|
| id, prospect_id, contact_id, user_id | |
| to_address, subject, sent_at | |

## prospect_contact_notes.csv - free text notes

| column | notes |
|---|---|
| id, prospect_id, contact_id, author_user_id | |
| body, created_at | |

## prospect_meetings.csv - booked meetings

| column | notes |
|---|---|
| id, prospect_id, contact_id, booked_by | |
| scheduled_at | |
| status | scheduled, done, no_show, cancelled |

## Relationships

```
profiles 1 --- * prospects.tusdr_assigned_user_id
prospects 1 --- * prospect_aliases, prospect_contacts, sdr_follow_up_tasks,
                  power_dialer_call_logs, email_activities, prospect_contact_notes,
                  prospect_meetings            (all via prospect_id)
prospects 1 --- * prospects.merged_into_id     (loser -> survivor)
prospect_contacts 1 --- * tasks / calls / emails / notes / meetings (via contact_id, optional)
```

## Output we expect from you

There is no `prospect_merge_audit.csv` in the input. The real system writes one row per merge
attempt; we expect your tool to produce the equivalent, for example `output/merge_audit.csv`
with at least: `request_id, survivor_code, loser_code, dry_run, status, details`. Shape is
yours to choose; what matters is that every decision is traceable.
