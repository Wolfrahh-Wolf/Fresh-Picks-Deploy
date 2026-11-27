# Estimation, Uncertainty, Risk and Spikes

How to size work relatively, state ranges, expose uncertainty and risk, and schedule spikes as planning items; assumes the Scrum Guide (November 2020 edition), the Kanban Guide (May 2025 edition), the Agile Alliance glossary entry on relative estimation (last modified 2022) and the Construx cone-of-uncertainty paper (version 1, 2010); checked 2026-11-26.

## Contents

- What an estimate is
- Choosing a method
- Relative sizing
- Ranges and the cone of uncertainty
- Forecasting from history
- Rolling task sizes into a plan estimate
- Risks
- Spikes in the plan
- Re-estimating
- Stating an estimate

## Guidance

### What an estimate is

An estimate is a forecast made with incomplete information. It is not a promise and not a target.

- The Scrum Guide says that in complex work what will happen is unknown, and only what has already happened is usable for forward-looking decisions; burn charts and similar tools help but do not replace that. The more you know about past performance, capacity and your Definition of Done, the more confident the forecast.
- A target is a desired outcome someone sets. If the user asks "can it be done by the end of the month", answer with the estimate and its confidence; do not turn the target into the estimate.
- Your estimate is a planning input. The coordinator and user decide scope, order and dates.
- If someone gives you a number to hit, record it as a constraint with its source and report the gap between it and your range.

### Choosing a method

| Situation | Use | Why |
|---|---|---|
| No history for this kind of work | Relative sizing against a reference task, with a range | Avoids false precision when nothing can calibrate hours or days |
| Closed task files of similar size exist | Forecast from throughput and elapsed time per task | The Scrum and Kanban guides both favour what has actually happened |
| Large unknown that blocks sizing | Spike first, then size | Estimates cannot be sharper than the definition they describe |
| Only a one-line idea exists | Order-of-magnitude range; do not size tasks | Early estimates are inherently wide (see the cone) |

Use more than one when you can; if they disagree, say so and explain the gap.

### Relative sizing

Relative estimation sizes items by comparison or grouping of items of equal difficulty, not in absolute time. The Agile Alliance entry lists benefits (less unwarranted precision, less temptation to confuse an estimate with a commitment) and also warns that the popular claim "people are better at relative than absolute estimation" is tentative, so use relative sizing for speed and honesty, not because it is proven more accurate.

1. Choose a reference: a small, well understood task already in the repository or in closed task files. Name it in the estimate. Call it size `S`.
2. Compare each new task to the reference: `S` (about the reference), `M` (clearly more files or one unfamiliar integration), `L` (several moving parts, or real uncertainty). Use a coarse scale; the gaps are deliberate so false precision is hard. Planning poker is another way to reach the same comparison when several people size together.
3. Anything bigger than `L` is not an estimate; it is a task to split or a spike to run. Anything you cannot compare to any known work is `unknown`, which means spike or open question.
4. Size what the task contains, including its tests and the work to make its check pass, not only the code.
5. Size the whole task, not the part you understand.
6. Do not convert sizes to hours or days. If history exists, convert through measured throughput (below), not through a fixed ratio.

Sizing drivers to look for in the repository before you pick:

| Driver | Raises the size when |
|---|---|
| Files and modules touched | More than a handful, or across ownership boundaries |
| Unfamiliar integration | Nothing similar already exists in the code |
| Data change | Schema or data migration is involved (design in `database-engineering`) |
| Test setup | Needs new fixtures, environments or external services |
| Ambiguity | Acceptance criteria are open or conflicting |
| Coupling | The change forces edits in code you do not own or understand |

### Ranges and the cone of uncertainty

Give a low, a likely and a high value. A single number hides what you do not know.

Construx's cone shows how wide estimates should be for skilled estimators at different points; it is a best case.

- At initial concept, estimates can be wrong by a factor of 4 either way (0.25x to 4x, a 16x spread).
- At approved product definition, error of 2x to 4x is still possible, so commitments made there cannot be supported.
- Most of the narrowing happens in roughly the first 20 to 30 percent of calendar time, and only because decisions remove variability: defining requirements, deciding what is out, designing the interface.
- With short iterations that move quickly through requirements and interface design, variability can fall to about 1.6x spread; with the front end settled and iterative delivery after, about plus or minus 25 percent.
- If decisions are not made, the cone becomes a cloud and never narrows. Extra weeks of "refining the estimate" without defining anything do not help.

Practical widths for a RelayCrew plan:

| State of the plan | Range to state |
|---|---|
| One-line idea, no PRD | Order of magnitude only; say the spread is up to 16x |
| PRD draft, no design, no task breakdown | Treat the high as at least twice the likely |
| Requirements agreed, design done, tasks verified-sized | Best case about plus or minus 25 percent; stay wider unless history supports it |
| Task in progress, scope stable | Re-estimate the remainder from what is done |

If you narrow a range, name the decision or fact that justified it. Do not narrow it to look confident.

### Forecasting from history

When enough similar tasks have finished, forecast from their real record instead of sizes. The Kanban Guide defines four metrics:

- **Throughput:** the number of items finished per unit of time, counted exactly.
- **Cycle time:** elapsed time from an item starting to finishing, as the team defines those points.
- **Work item age:** elapsed time since an unfinished item started.
- **WIP:** items started but not finished.

The Kanban Guide's service level expectation (SLE) combines a time and a probability taken from historical cycle time, for example "85% of items finish in eight days or less", and says a best guess will do until enough data exists.

How to use it here:

1. Choose a start and finish definition for a task (for example plan approved to acceptance criteria verified).
2. Collect the elapsed time of closed, comparable tasks from the task files and version-control history. A dozen or more similar items is a reasonable minimum for percentiles (rule of thumb, unverified); with fewer, say so and widen the range.
3. State the forecast as a percentile range: "50% of similar tasks finished within 2 days, 85% within 5".
4. For a set of N similar tasks, project from observed throughput per week and give a range, not a date.
5. Warn when tasks differ greatly in size: counting items only works when items are roughly alike, which is another reason to keep tasks small.
6. Watch work item age during execution: an item far past the 85th percentile is a signal to replan or escalate.

A Monte Carlo simulation over past throughput is a common refinement; this skill does not require it (not verified against a primary source).

### Rolling task sizes into a plan estimate

- Sum the lows, the likelies and the highs of the tasks, stating the numeric weight you give each size (for example S=1, M=3) because sizes are relative and the weights are your own convention. The sum of lows to the sum of highs is a wide bound. Random errors partly cancel across many tasks, but bias (for example, all tasks sharing one unknown) does not, so identify shared drivers and call them out.
- Add no hidden padding to individual tasks. Show uncertainty as a range and list what drives the high end.
- Include spikes and approval waits. A task that needs user approval cannot start until the user answers; list the wait as a dependency, not as effort.
- The 12-task limit applies. If the roll-up shows more than 12 tasks, re-scope before reporting an estimate.
- Report the critical path separately from the total effort; parallel work shortens elapsed time but not effort.

### Risks

A risk, in the Kanban Guide's wording, is the chance that something bad could happen. List the few that could change the plan, not every worry.

| Category | Typical examples | Typical response |
|---|---|---|
| Technical unknown | Library behaviour not verified, new integration | Spike first; size after |
| External dependency | Third-party limits, another team's API | Move early; add decision or approval dependency |
| Requirement volatility | Open questions, conflicting statements | Resolve with the user before sizing the affected tasks |
| Data and migration | Shared tables, large backfills | Rollback step, test copy, approval gate; see `database-engineering` |
| Security | Authentication, payments, personal data, new input | Mark high risk; security-auditor required; see `security-engineering` |
| Environment | Test environments, credentials, tooling | Name the owner and the need before starting |

Risk list format:

| ID | Risk | Likelihood (L/M/H) | Impact (L/M/H) | Trigger | Response | Plan effect |
|---|---|---|---|---|---|---|

Responses: avoid (reorder or cut scope), reduce (spike, thin slice first), hand to the user (decision or approval), accept (record it). Rank by likelihood and impact together; plan the top three to five. A risk that blocks sizing becomes a spike. Anything high impact and unresolved goes into the Summary and open questions.

### Spikes in the plan

A spike is time-boxed work to learn something so that a story can be sized or split, not to deliver the feature. Cohn's SPIDR describes it as research that may include prototyping; the team is building knowledge, not the functionality. Wake adds that a story can be split into a time-boxed spike that gives enough information to estimate, and the rest that builds the feature.

Plan a spike when:

- You cannot compare a task to anything known and the uncertainty is high impact.
- A decision (technology, approach) changes the shape of later tasks.
- You are baffled about how to split a story after trying the other splitting patterns.

Write each spike as:

```
Spike S1: <one-sentence question>
Questions (1 to 3): <specific, answerable>
Time-box: <number of tasks or hours; a hard stop>
Output: <written answer, evidence, recommended option>
Decision it unlocks: <which tasks it lets you size or split>
Exit: stop at the time-box even if unanswered; report what is still unknown
```

Rules for the plan:

- Put spikes at the front, before the tasks they unblock.
- Size a spike by its time-box, not in points. An Agile Alliance community post argues that pointing spikes inflates the apparent amount of delivered value and hides struggle; the opinion is the author's, but the sizing-by-time-box rule is sound either way.
- A spike produces knowledge, not delivered value. Do not count it toward delivered work.
- Persistent spikes in plan after plan signal deeper design or technology uncertainty; report that as a risk.
- A spike never changes the product, ships code or touches shared systems. For spike execution, proof-of-concept rules, and go or no-go evidence load `technical-research`.

### Re-estimating

- Re-estimate when a spike finishes, when a task completes far from its range, when scope changes, and when a risk fires.
- Show the old range, the new range and the reason. Do not overwrite history silently.
- If tasks keep finishing outside their ranges, say what is systematically wrong (for example, the reference task is not comparable) and re-calibrate.
- Late in the work, estimate the remainder from what is left and from what has been finishing, not from the original sizes.

### Stating an estimate

Always include: what is estimated, basis, range, confidence, assumptions, the drivers of the high end, and the next step that would narrow it.

```
Estimate (planning forecast, not a commitment)
Scope: reminder emails for overdue invoices (FR-1, FR-2, FR-3; FR-4 excluded)
Basis: relative sizes against reference task <path>; no throughput history (uncalibrated)
Tasks: 6 (3 S, 3 M); critical path T2, T3, T4, T5
Range: low 9 / likely 12 / high 21 size points (roll-up weights stated: S=1, M=3)
Confidence: medium-low
High-end drivers: T4 (provider limits unknown until T1), T2 (shared-table migration needs approval)
Assumptions: A1 invoices store due dates in UTC (unverified); A3 existing email provider stays
Next to narrow: finish spike T1; expect the high end to fall by about 6 if limits are generous
```

## Examples

### Relative sizing against a reference

Reference: task "add a nullable field to the invoice list endpoint with a test" (size `S`, 2 files).

| Task | Comparison | Size | Note |
|---|---|---|---|
| Store one reminder rule | Same pattern as reference, new table | S | Migration separately sized in its own task |
| Send reminder email through provider | New integration, tests with a test inbox | M | Provider limits unknown |
| Idempotent job | One file plus one test | S | Needs the sent-record table |
| Real-time delivery status via webhook | No comparison; unknown provider behaviour | unknown | Spike or open question |

### A range narrowing after a spike

| Moment | Range (size points) | Reason |
|---|---|---|
| Before spike | 9 to 21 | Provider limits unknown |
| After spike S1 | 9 to 15 | Provider batches 500 messages and supports scheduling; T4 is plain M |
| After T4 finishes | remainder 4 to 7 | T5 and T6 now compared with T4's actual effort |

### Bad estimate to good estimate

| Bad | Good |
|---|---|
| "About 3 days." | "Likely 5 tasks of size S to M; 50% of similar past tasks closed within 2 days, 85% within 5; high end if provider limits force batching" |
| "13 story points, done by Friday." | "Likely 13 size points; range 9 to 22. No date: no throughput history yet" |
| "Two weeks, I added buffer." | "Likely 8 tasks; the high end adds the migration approval wait; assumptions A1 and A3" |

### Risk list, filled

| ID | Risk | L | I | Trigger | Response | Plan effect |
|---|---|---|---|---|---|---|
| R1 | Provider cannot schedule sends | M | H | Spike T1 answer is no | Run T1 first; fallback: own scheduler job | Adds one M task if triggered |
| R2 | Migration on shared table locks writes | L | H | Test copy shows long lock | Test on realistic data; ask user for a window | T2 gate; rollback verified |
| R3 | Complaint target not agreed | M | M | Q2 unanswered at start of T4 | Ask user; use A2 until answered | None if answered, otherwise G2 stays open |

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reporting a single number | Hides uncertainty and invites commitment | Give low, likely and high with a basis |
| Treating the estimate as a commitment or target | Pressure replaces learning | Say forecast, list assumptions and confidence |
| Converting sizes to days with a fixed ratio | Sizes are relative; the ratio is invented | Use measured throughput or cycle time, or give no date |
| Estimating before requirements or decisions exist | The cone is at its widest; precision is false | State order of magnitude and resolve decisions first |
| Narrowing a range without a reason | Confidence looks good, then breaks | Name the decision or fact that justifies it |
| Padding every task | Hides real risk and wastes time | Keep ranges honest and list high-end drivers |
| Sizing only the code | Misses tests, setup and fixes | Size the task including its verification |
| Pointing spikes or counting them as delivered | Hides lack of delivered value | Time-box spikes and report them separately |
| Ignoring approval waits | Elapsed time is underestimated | List approvals as dependencies |
| Using throughput on tasks of very different size | The forecast misleads | Slice tasks to similar size first |

## Checklist

- [ ] The estimate states what it covers and what it excludes.
- [ ] A reference task is named, or the estimate says it is uncalibrated.
- [ ] Every size is `S`, `M`, `L` or `unknown`, and nothing larger than `L` remains.
- [ ] Every `unknown` has a spike or an **open** question with an owner.
- [ ] The estimate gives low, likely and high values with a basis.
- [ ] The range width matches the state of the plan, or the reason for a narrower range is named.
- [ ] No date is given unless it comes from measured throughput.
- [ ] Assumptions are listed and marked **unverified** where not confirmed.
- [ ] The top risks have a likelihood, impact, trigger and response.
- [ ] Every spike has a question, a time-box, an output and an exit.
- [ ] Approval waits appear as dependencies, not effort.
- [ ] The estimate names what would narrow it next.
- [ ] The plan has at most 12 tasks.

## Verify with context7 and gh_grep

- **context7:** before sizing work that depends on a library, framework or service, query the exact version from the manifest for the facts that drive size: "`<service>` rate limits and batching", "`<library>` `<version>` migration guide", "`<framework>` known limitations of `<feature>`". Pure relative sizing against tasks already in the repository needs no query; say so.
- **gh_grep:** when comparing an unfamiliar integration to known work, search literal code for its call or configuration key (for example the constructor name plus an adjacent test or migration file name) in maintained projects and count how many files and tests a typical integration touches. Use that to choose `S`, `M` or `L`; do not copy code.

## Sources

- The 2020 Scrum Guide (forecasting, sizing by developers, past performance, Definition of Done): https://scrumguides.org/scrum-guide.html
- The Kanban Guide, May 2025 (flow metrics, service level expectation, definition of risk): https://kanbanguides.org/the-kanban-guide/2025.5
- Relative Estimation, Agile Alliance glossary: https://agilealliance.org/glossary/relative-estimation/
- Software Development's Cone of Uncertainty, Steve McConnell, Construx, version 1, 2010: https://www.construx.com/wp-content/uploads/2019/02/CxWhitePaper_ConeOfUncertainty.pdf
- SPIDR: Five Simple but Powerful Ways to Split User Stories (spikes), Mike Cohn, Mountain Goat Software: https://www.mountaingoatsoftware.com/agile/five-simple-but-powerful-ways-to-split-user-stories
- INVEST in Good Stories, and SMART Tasks (spikes for estimability), Bill Wake, 2003: https://xp123.com/invest-in-good-stories-and-smart-tasks/
- The Practice of Sizing Spikes with Story Points (community opinion post), Gregory Engel, Agile Alliance, 2018: https://agilealliance.org/the-practice-of-sizing-spikes-with-story-points/
