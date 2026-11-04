# Product Engineer case: duplicate companies in the 1P prospect database

Thank you for taking the time. This case is a simplified version of a real problem we solved
at InsideJob AI. There is no single correct answer. We care about how you reason about the
business, what you decide to do and what you decide NOT to do, and how clearly you explain it.

Time guidance: 3 to 5 hours. Please do not spend more. AI tools are allowed and encouraged;
we only ask that you understand and can defend every line you ship.

## 1. The business in two minutes

InsideJob AI runs outbound sales for US manufacturers. Our team of SDRs (sales development
reps) calls and emails small manufacturing shops to book intro meetings.

Everything lives in one internal system we call "the OS". The part that matters here is the
1P (first-party) prospect database:

- `prospects` is the list of companies. One row per company. Each row has a human code
  (`P-000123`), a website, a phone, up to 3 emails, a city/state, a pipeline `status`, and
  optionally an assigned SDR (`tusdr_assigned_user_id`).
- SDRs only see companies that are assigned to them or that have an open follow-up task.
  Everything an SDR does - calls, emails, notes, meetings, follow-up tasks - hangs off the
  company row.
- The company list is fed by data imports from several providers. Different providers describe
  the same shop differently ("Cedar Tool & Die" vs "Cedar Tool and Die Co.", with or without
  `www`, phone in different formats, one row without a website, etc.).

## 2. The problem

Imports have created duplicate company rows. The consequences are concrete:

- Two SDRs call the same shop on the same week without knowing it.
- A contact added on one row is invisible from the other row.
- A "follow-up" promised to the owner sits on a row nobody is looking at.
- The same company is counted twice in pipeline numbers.

Some duplicates were already "merged" by an older process that only set `merged_into_id` on
the losing row and never cleaned anything else up. Those rows are still visible to SDRs.

## 3. What we are asking you to build

A small, reviewable tool (CLI, script, notebook, small service - your choice) that:

1. Finds duplicate groups in the seed data and explains WHY each group is a duplicate.
2. For each group, proposes a survivor and a merge plan: which row survives, what moves
   (contacts, tasks, calls, emails, notes, meetings), what gets filled in on the survivor,
   and what cannot be decided automatically.
3. Can apply a merge safely (dry-run first, then real), leaving an audit trail in
   `prospect_merge_audit`, and leaving the loser row findable (archived, not deleted).
4. Makes sure SDRs do not lose work: pending follow-ups, contacts marked do-not-call, booked
   meetings must survive the merge.

Rules of the business that you should respect (these are real):

- Identity of a company is, in order: root website domain; if no website, main phone number.
  Generic domains (gmail.com, yahoo.com, etc.) do NOT identify a company.
- Merge is fill-only: never overwrite a non-empty field on the survivor with the loser's value.
- Never delete. Losers get `merged_into_id` + `archived_at` and stay in the table.
- The old name of a loser must remain searchable (see `prospect_aliases`).
- When something needs a human decision, say so and stop. Do not guess.

Not in scope (please do not build this): a UI, authentication, a scheduler, a generic
fuzzy-matching library for company names.

## 4. What you get

```
schema.sql              simplified Postgres schema (mirrors the real tables)
data/seed.sql           65 companies, contacts, tasks, calls, emails, notes, meetings
data/*.csv              same data as CSV if you prefer pandas / DuckDB / anything
docker-compose.yml      one-command Postgres with schema + seed loaded
```

Run it:

```bash
docker compose up -d
psql postgresql://postgres:postgres@localhost:55432/onep_case -c "select count(*) from prospects"
```

Some rows in the seed are duplicates, some only look like duplicates, and a few are
pre-existing data problems. Part of the exercise is telling them apart.

## 5. What to send back

A repo link (public or shared with us) with:

- Your code.
- A short `NOTES.md` (one page max): the duplicate groups you found and what you decided for
  each; what you did not do and why; what you would do differently with more time; and
  anything in the data you think we should know about.

## 6. How we evaluate

We will read your NOTES.md first, then your code, then run it against the seed. We look at:

- Did you understand the business flow (SDR work must not get lost; fill-only; archive not
  delete)?
- Is the solution as simple as the problem allows? Simple and correct beats clever.
- Did you tell apart real duplicates, false positives and data bugs?
- Did you stop and ask when a human decision was needed instead of guessing?
- Can we read your code and your notes in 20 minutes and know exactly what happened?

In the final conversation we will ask you to make a small change to your solution live, so
build something you can move around in comfortably.

Questions during the case are welcome - email the person who sent you this link.
