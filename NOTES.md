# NOTES

How to run: `python3 -m unittest -v` (tests) and `python3 -m dedup groups` (CLI). Python 3 standard library only, nothing to install.

## Duplicate groups found and what I decided

_(filled in as each step is built)_

Survivor rule (the README leaves it to us): the row furthest along the pipeline wins, because merge is fill-only and the survivor keeps its status; picking a less advanced row would erase sales progress. Ties go to the row with an assigned SDR, then to the oldest row. A row that already lost a merge (`merged_into_id` set) never survives, so earlier merges are respected.

A group is not merged, and goes to review, when a person has to decide:
- Different SDRs own rows of the company: who keeps the account is a business decision.
- More than 3 different emails: there are only 3 slots, and choosing which email to drop is not the tool's call.
- Rows use different hosts of the same root domain (e.g. `waco.zenithstamping.com` and `zenithstamping.com`): they can be separate plants with their own contacts.

When a group merges, every row that hangs off a loser (contacts, follow-up tasks, calls, emails, notes, meetings, aliases) is re-pointed to the survivor. History moves too, not only pending work: an SDR opening the survivor must see every call already made to that shop. Moving only changes `prospect_id`, so pending tasks, do-not-call flags and booked meetings arrive exactly as they were.

Merge is fill-only: a loser value goes into the survivor only when the survivor's field is empty, never over a value it already has. Only company data fills (website, phones, city, state, employee count, assigned SDR); identity, status, timestamps and merge history (`merged_into_id`, `archived_at`) never do, otherwise a loser that lost an earlier merge would mark the survivor as merged. Loser emails go to the survivor's first free email slot, skipping ones it already has; if no slot is free the merge refuses instead of dropping an email (the email blocker stops those groups first).

Never delete: a loser stays in `prospects.csv` with `merged_into_id` pointing straight to the survivor (a loser from an older chained merge is re-pointed, so one hop always lands on a live row) and `archived_at` set to the merge time (an earlier `archived_at` is kept). Its name is added to `prospect_aliases` as `historical_merge`, unless the survivor can already be found by that name.

Audit: `output/merge_audit.csv` gets one row per merge attempt, blocked attempts included, with `request_id, survivor_code, loser_code, dry_run, status, details`. Status is `merged`, `planned` (dry run) or `needs_review`. `details` says why the rows matched and what changed (rows moved per table, fields filled, alias added), or why a person has to decide, with user names instead of ids.

Output: a real run writes every table to `output/` with the same columns as the input; a dry run writes only the audit. The audit file is append-only, so dry runs and real runs both stay in the trail. The writer refuses to write into or inside `data/`.

## What I did not do, and why

- No external libraries: standard library only, so the tool runs with nothing to install.
- `phone_secondary` does not identify a company. The rule says "main phone number", so only `phone` is used.

## What I would do differently with more time

- Root domain is "the last two labels of the host" and a phone is "ten digits, US country code dropped". Both fit this dataset (US shops on .com/.net/.us). In production I would use the Public Suffix List and `phonenumbers` instead.

## Things in the data you should know about
