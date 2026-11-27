# PRD Structure and Upkeep

How to write and maintain `docs/PRD.md` using the RelayCrew template headings, with goals, non-goals and success measures; assumes the Scrum Guide (November 2020 edition) for the Product Goal idea and the Construx cone-of-uncertainty paper (version 1, 2010) for commitment timing; checked 2026-11-26.

## Contents

- Purpose, ownership and status
- Template sections at a glance
- Problem and users
- Goals and success measures
- Non-goals
- Requirement rows, IDs and priority
- Constraints, assumptions and open questions
- Writing a new PRD from a brief
- Upkeep: changing the PRD after work happens
- What does not belong in the PRD

## Guidance

### Purpose, ownership and status

The PRD records what the product must do and why, in terms a user can confirm. It does not say how to build it. The architect owns it; the user approves it.

- The template starts with `Status: draft`. Leave it as `draft` while you work. Never mark requirements approved yourself.
- When the PRD is ready, say "ready for user approval" in the Summary. If the user then tells you to record approval, change the line to `approved <date>` and say in the report that you did so on their instruction.
- The project's existing PRD wins over this guidance. Keep its headings, IDs and style; add missing template sections rather than reorganising.
- A PRD is not a commitment to a date. Commitments made while scope is still vague cannot be supported (Construx). Keep dates out of the PRD unless the user supplied a fixed external deadline; then record it under Constraints.

### Template sections at a glance

| Section | Holds | Quick test |
|---|---|---|
| Problem | Who is affected, what goes wrong, what it costs | Still true if you delete every mention of a solution |
| Users and use cases | Named user types and what each needs to do | Every use case maps to at least one requirement row |
| Goals and success measures | Outcomes with a target and a way to measure | Someone could tell next quarter whether it worked |
| Non-goals | Things a reader might expect that are deliberately excluded | Each has a reason |
| Functional requirements | Table: ID, requirement, priority, acceptance criteria | One behaviour per row |
| Non-functional requirements | Table: ID, quality, target, how verified | Each target is a number or marked **open** |
| Constraints and assumptions | Fixed limits and unverified beliefs | Each assumption says how to check it |
| Open questions | Numbered decisions only the user can make | Each has an impact and a default |

### Problem and users

- Write the problem as one short paragraph: who, what goes wrong today, the observable consequence. Use evidence from the brief, the repository or the user; mark anything else **unverified**.
- Do not describe features here. If the problem statement only makes sense with a feature name in it, rewrite it.
- List user types as roles the product actually distinguishes (for example "billing admin", "customer"). Three to seven use cases, each a verb phrase from the user's side.
- Do not invent personas, quotes or statistics. Missing information becomes an open question.

For eliciting needs and resolving ambiguity, load `requirements-engineering`.

### Goals and success measures

A goal is an outcome for users or the business, not a feature. A success measure says how you will know. The Scrum Guide describes a Product Goal as the long-term objective the team works toward and finishes or abandons before taking the next; use that as the model for the first goal.

1. Write one Product Goal sentence at the top of the section: the future state the work aims at.
2. Give each goal an ID (`G1`, `G2`). Keep to five goals or fewer; more means the PRD covers several products.
3. For each goal write at least one measure with all five parts:

| Part | Meaning | Example |
|---|---|---|
| Metric | What is counted | Share of invoices paid within 14 days of due date |
| Baseline | Value today, or **open** if unknown | 61% over the last full quarter |
| Target | Value that counts as success | 75% |
| Window | When it is judged | 60 days after release |
| Source | Where the number comes from | Payments table, weekly query |

4. Prefer a measure the project can compute from data it already has. If it needs new instrumentation, that instrumentation is a requirement row.
5. Add one guardrail measure when a goal could be met by harming something else (for example complaint rate for a reminder feature).
6. Never state a target you invented. If the user did not give one, propose a value labelled as an assumption and add an open question.

Bad measures: "improve user experience", "increase engagement", "ship the dashboard". The first two have no metric; the third is an output, not an outcome.

### Non-goals

Non-goals stop scope creep and make deferrals visible. They are the home for everything you cut when slicing stories.

- Include things a reasonable reader would expect and the plan excludes: adjacent features, platforms, user types, scale levels, integrations.
- For each, give a reason and, where it helps, a revisit trigger ("revisit if more than a third of sessions are on phones").
- A non-goal is not the opposite of a goal and not a defect list. "No bugs" is not a non-goal.
- Every PRD above a one-screen change has at least one non-goal. If you cannot think of one, you have not looked at what was cut.
- Moving an item from non-goals into requirements is a scope change; report it.

### Requirement rows, IDs and priority

Use the template tables as they are. Do not add columns.

- IDs: `FR-1`, `FR-2` for functional rows; `NFR-1`, `NFR-2` for non-functional rows. Assign the next free number. Never renumber, never reuse a retired ID.
- One behaviour or one quality per row. A row containing "and" between two behaviours is two rows.
- Phrase the requirement from the user's side: "A billing admin can disable reminders for one customer", not "Add a boolean column".
- Priority uses `must`, `should` or `could`. A `won't` goes to Non-goals. Define the meaning once under Constraints if the project has not: `must` blocks release, `should` is expected, `could` is dropped first.
- Link rows to goals in the requirement text with the goal ID, for example "(G1)". A row with no goal needs a reason or removal.
- The Acceptance criteria cell holds a short observable summary; the detailed criteria live in the task file. Rules for writing them belong to `requirements-engineering`.
- Non-functional rows need a measurable target and a verification method, or are marked **open**. For target-setting load `requirements-engineering`.
- Stories can live as functional rows. There is no separate stories file; do not create one unasked.

### Constraints, assumptions and open questions

- **Constraint:** a fixed limit from outside the plan: budget, external deadline, regulatory rule, mandated stack, existing integration. State its source.
- **Assumption:** something you believe but have not confirmed. Write it as `A1: <statement>. Check: <how>. If false: <consequence>.` Mark it **unverified**.
- **Open question:** a decision only the user can make. Number them `Q1`, `Q2`. Each states the impact and the default you will use if unanswered.
- Resolve a question by moving the answer into the right section and deleting the question. The PRD describes what is true now, not the conversation history.
- Costly-to-reverse decisions (new dependency, auth model, public API shape) also need an ADR; for that load `system-architecture`.

### Writing a new PRD from a brief

1. Read the brief, existing docs, `docs/MEMORY.md` and the code. List facts, assumptions and unknowns separately.
2. Draft Problem and Users from facts only.
3. Draft goals and measures; mark missing baselines and targets **open**.
4. Draft non-goals from what the brief implies but does not ask for.
5. Draft requirement rows from use cases, one behaviour each, with goal links.
6. List constraints, assumptions and open questions.
7. Ask blocking questions together; otherwise state assumptions and continue.
8. Run the checklist below. Report "ready for user approval".

### Upkeep: changing the PRD after work happens

- Update the PRD in the same task that changes product behaviour, as part of documentation sync, not later.
- Compare it with what was built. If the code departs from the approved PRD, report the difference and ask which is right. Never edit the PRD to match the code, or the code to match the PRD, silently.
- Edit rows in place and keep IDs. If a requirement is dropped on purpose, delete the row and add a non-goal with the reason. Gaps in numbering are fine.
- When a requirement is split during planning, keep the original ID on the first part and assign new IDs to the rest.
- Do not mark a requirement as done in the PRD. Delivery status lives in `docs/TASKS.md` and the task file.
- If a change to goals or non-goals is large, say so in the Summary; the user decides whether the PRD needs re-approval.

### What does not belong in the PRD

| Content | Goes to | Owner |
|---|---|---|
| Screens, flows, visual rules | `docs/DESIGN.md` | architect |
| Components and data flow | `docs/ARCHITECTURE.md` | architect |
| Tables and relationships | `docs/DB.md` | architect |
| Endpoints and payloads | `docs/API-CONTRACTS.md` | architect |
| Reasons for a costly decision | `docs/adr/` | architect |
| Task status | `docs/TASKS.md` | coordinator |
| Durable lessons and constraints discovered while working | `docs/MEMORY.md` | coordinator |

## Examples

### Filled PRD for a small feature

The figures are illustrative, not real project data.

~~~~markdown
# Product Requirements

Owner: architect. Status: draft

## Problem
Billing admins chase overdue invoices by hand. About 4 in 10 invoices are paid more than 14 days late, and admins spend their Monday mornings writing emails.

## Users and use cases
- Billing admin: sets how reminders work, sees what was sent.
- Customer contact: receives reminders and can stop them.

## Goals and success measures
Product Goal: overdue invoices are chased automatically and politely.

| ID | Goal | Metric | Baseline | Target | Window | Source |
|---|---|---|---|---|---|---|
| G1 | Customers pay sooner | Share of invoices paid within 14 days of due date | 61% (last full quarter) | 75% | 60 days after release | Weekly query on payments |
| G2 | Reminders are not a nuisance | Reminder-related complaints per 1,000 reminders | open | at most 2 (assumption A2) | 60 days after release | Support tags |

## Non-goals
- SMS and phone reminders. Reason: email covers the cost-benefit case; revisit if email open rate is below 30%.
- Per-customer custom wording. Reason: one template is enough to test G1.
- Reminders for invoices under 20 in any currency. Reason: collection cost exceeds the amount.

## Functional requirements
| ID | Requirement | Priority | Acceptance criteria |
|---|---|---|---|
| FR-1 | A billing admin can enable one reminder rule (days after due date) for all customers (G1) | must | Enabled rule sends one email per overdue invoice on the due day plus N |
| FR-2 | A customer contact can stop reminders for an invoice from a link in the email (G2) | must | Link stops further reminders; repeat click is harmless |
| FR-3 | A billing admin can disable reminders for one customer (G2) | should | Disabled customer receives nothing; others unaffected |
| FR-4 | A billing admin can see a log of reminders sent (G1) | could | Log lists invoice, date, outcome |

## Non-functional requirements
| ID | Quality | Target | How verified |
|---|---|---|---|
| NFR-1 | Delivery timeliness | Reminder sent within 15 minutes of schedule time | Timestamp comparison in integration test |
| NFR-2 | Idempotency | No invoice receives two reminders for the same rule and day | Test that runs the job twice |

## Constraints and assumptions
- Constraint: use the existing email provider; no new paid service without approval.
- A1: Invoice due dates are stored in UTC. Check: read `DB.md` and the schema. If false: scheduling rules need time zones. unverified
- A2: Two complaints per 1,000 is acceptable to the user. Check: Q2. unverified

## Open questions
1. Q1: Should reminders stop when a payment is partially made? Impact: FR-1 logic. Default: keep sending until fully paid.
2. Q2: What complaint rate is acceptable? Impact: G2 target. Default: A2.
~~~~

### Success measure: bad to good

| Bad | Good |
|---|---|
| "Improve checkout experience" | "Checkout completion rate rises from 58% to 65% within 45 days of release, measured from the orders and sessions tables" |
| "Make the API faster" | "p95 latency of `GET /reports` falls from 1.8 s to under 600 ms at 50 concurrent users, measured by the load-test script" |
| "Ship the new dashboard" | "Support leads resolve a stalled-ticket lookup in under 30 s, measured by a timed task with three leads" |

### Non-goal: bad to good

| Bad | Good |
|---|---|
| "No bugs" | "No bulk import in this release. Reason: manual entry covers the first 200 customers; revisit when onboarding exceeds that" |
| "Not mobile" | "No native mobile app; the web UI is responsive down to 360 px width. Reason: usage data shows 8% mobile sessions" |

### Requirement row: bad to good

| Bad | Good |
|---|---|
| "Add `reminder_rule` table and cron job" | "A billing admin can enable one reminder rule (days after due date) for all customers (G1)" |
| "Users can manage reminders and view logs and export them" | Three rows: manage rule, view log, export log, each with its own priority |

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Writing features into Problem | The PRD cannot be judged against the problem | State who suffers what; move features to requirement rows |
| Goals without baseline, target or source | Nobody can tell whether the product worked | Fill all five measure parts or mark the gaps **open** with a question |
| Invented numbers presented as targets | The user may approve a figure that no one chose | Label as assumption, add an open question |
| No non-goals | Scope creeps; deferrals vanish | List what was cut while slicing, with reasons |
| Renumbering IDs after edits | Task files and tests point at the wrong rows | Never reuse or shift IDs; gaps are acceptable |
| Setting `Status: approved` yourself | Breaks the rule that only the user approves | Report "ready for user approval" |
| Design and schema detail inside the PRD | Duplicated truth that drifts | Link to the owning doc and keep one source |
| Editing the PRD to match the code | Hides a possible defect or a missed decision | Report the difference and ask which is right |
| Adding a dated roadmap | Commits to dates while uncertainty is widest | Keep dates only as sourced constraints |

## Checklist

- [ ] The Problem paragraph still reads true with all solutions removed.
- [ ] Each goal has an ID and at least one measure with metric, baseline, target, window and source, or the gap is marked **open**.
- [ ] There is a guardrail measure wherever a goal could be met by causing harm elsewhere.
- [ ] At least one non-goal exists, each with a reason.
- [ ] Every functional and non-functional row has a unique ID that was never used before.
- [ ] Every row states one behaviour or quality, from the user's side.
- [ ] Every requirement row links to a goal or states why it has none.
- [ ] Every non-functional row has a numeric target and a verification method, or is marked **open**.
- [ ] Every assumption says how to check it and is marked **unverified**.
- [ ] Every open question is numbered, owned by the user and has a default.
- [ ] No design, schema or endpoint detail is duplicated from another doc.
- [ ] `Status` is still `draft` unless the user instructed otherwise.

## Verify with context7 and gh_grep

- **context7:** only for constraints that cite a tool. Before writing a constraint such as a rate limit, supported platform or supported version, query the exact library or service at the version in the manifest: "`<service>` rate limits per account", "`<library>` `<version>` supported runtimes". A PRD that only restates project facts needs no query; say so in the report.
- **gh_grep:** to see how maintained projects phrase PRD sections, search for the literal heading `## Non-goals` in markdown files named `PRD.md`, and compare how goals and measures are written. Use results as wording examples only; do not copy text without a compatible licence.

## Sources

- The 2020 Scrum Guide (Product Backlog, Product Goal, Definition of Done): https://scrumguides.org/scrum-guide.html
- INVEST in Good Stories, and SMART Tasks (testability of requirements), Bill Wake, 2003: https://xp123.com/invest-in-good-stories-and-smart-tasks/
- Software Development's Cone of Uncertainty (commitment timing), Steve McConnell, Construx, version 1, 2010: https://www.construx.com/wp-content/uploads/2019/02/CxWhitePaper_ConeOfUncertainty.pdf
