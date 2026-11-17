# NOTES

Run with Python 3, standard library only: `python3 -m unittest` (unit + CLI acceptance tests), `python3 -m dedup groups` (read-only view), `python3 -m dedup dry-run` (audit only), `python3 -m dedup apply` (writes `output/`). `data/` is never written.

## Duplicate groups and what I decided

| Group | Rows (survivor first) | Decision |
|---|---|---|
| keystonespring.com | P-000003 ← P-000046 | Merged. Finishes an old merge: P-000046 pointed to P-000003 but was still visible. |
| anchorforge.com | P-000048 ← P-000058, P-000059 | Merged. Old chain 59 → 58 → 48 flattened to 48; P-000059 has no website and matched by phone. |
| cedartool.com | P-000029 ← P-000032 | Merged. P-000029 has the booked meeting. |
| harborprecision.com | P-000063 ← P-000030 | Merged. |
| granitecastings.net | P-000025 ← P-000006 | Merged by main phone (P-000006 has no website). Its pending callback moves to P-000025, same SDR. |
| summitlaser.com | P-000057, P-000017, P-000018 | **Needs review**: owned by Casey Rowe and Jordan Pike. |
| juniperrubber.com | P-000062, P-000024 | **Needs review**: owned by Morgan Tate and Jordan Pike. P-000024 has a do-not-call contact and a pending task. |
| zenithstamping.com | P-000044, P-000027 | **Needs review**: `waco.` subdomain, different city and phone; probably two plants. |
| beaconcoatings.com | P-000061, P-000060 | **Needs review**: 4 different emails, only 3 slots. |

Rules I chose (the README leaves them open):
- **Identity**: root domain, else main phone (10 digits). Generic domains don't count. A row with a website never joins by phone.
- **Survivor**: furthest pipeline status (merge is fill-only, so the survivor keeps its status), then assigned SDR, then oldest. A row that already lost a merge never survives.
- **Stop and ask** (nothing touched, `needs_review` in the audit): different SDRs, more than 3 emails, different hosts of one domain, a phone shared by several domains, no website and no phone, no possible survivor.
- **Merge**: every child row (contacts, tasks, calls, emails, notes, meetings, aliases) moves to the survivor, history included. Company fields are fill-only; emails go to free slots. The loser keeps its row, gets `merged_into_id` straight to the survivor and `archived_at`, and its name becomes a `historical_merge` alias.
- **Audit**: one row per attempt, blocked ones included, append-only, user names instead of ids.

## What I did not do, and why

- No name matching: out of scope, and names are the least reliable signal here.
- `phone_secondary` is not used for identity: the rule says main phone.
- I did not choose an owner for groups with two SDRs, or drop an email: those are business decisions.
- I did not fix P-000015 (see below): it is not a duplicate, so a person should decide.
- No external libraries, so it runs with nothing to install.

## With more time

- Public Suffix List and `phonenumbers` instead of "last two labels" and "ten digits" (fine for these US shops).
- A small decisions file for the review queue (chosen survivor or owner) that `apply` reads, so blocked groups can be merged after a person decides.
- A data-quality report (self-merges, merged rows still visible) next to the audit.
- Set `updated_at` on the rows a merge touches.

## Things in the data you should know

- **P-000015** has `merged_into_id` pointing to itself and is still visible to SDRs.
- P-000046, P-000058 and P-000059 were "merged" by the old process but never archived (fixed by `apply`).
- P-000007 and P-000054 share a phone but have different websites: not duplicates. A note says the number rings at a rep who covers several shops, and a call to P-000054 got `bad_number`.
- P-000047 and P-000053 have `gmail.com` as website: treated as no website; their phones differ.
- Contact names and emails repeat across unrelated companies (e.g. `chris@example-mail.com` on P-000006 and P-000059), so they are never used to identify a company.
