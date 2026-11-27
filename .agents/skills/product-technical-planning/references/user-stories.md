# User Stories, INVEST and Vertical Slicing

Story format, the INVEST test, vertical slicing and splitting patterns for work that is too large to plan; assumes Bill Wake's INVEST article (2003), the Humanizing Work story-splitting flowchart (nine patterns, poster last updated 2018), Mike Cohn's SPIDR article (updated August 2026) and the Scrum Guide (November 2020 edition); checked 2026-11-26.

## Contents

- Story format and what a story is for
- When something is not a story
- INVEST as a working test
- Vertical slicing
- Preparing a story before you split it
- Splitting patterns
- Choosing a pattern
- Evaluating a split
- How much detail, and when
- Where stories live in RelayCrew

## Guidance

### Story format and what a story is for

A story is a small, negotiable statement of something a user can do and why it matters. It is a prompt for a conversation and for tests, not a specification.

```
As a <user type from the PRD>, I can <capability>, so that <outcome>.
```

- The user type must exist in `docs/PRD.md` under Users and use cases. If it does not, add it there or ask.
- The capability is observable behaviour. The outcome is the value; if you cannot state one, the item is probably a task.
- Wake, crediting Ron Jeffries, describes three parts: the card (the short statement), the conversation (details agreed while working) and the confirmation (the tests). Keep the statement short and let notes, test ideas and open questions accumulate under it.
- Link each story to the requirement IDs it covers (`FR-3`) and to the goal it serves (`G1`).
- Acceptance criteria for a story follow the rules in `requirements-engineering`; do not write them to a looser standard here.

### When something is not a story

| Item | What it is | Handle as |
|---|---|---|
| "Create the reminders table" | Technical enabling work | A task inside the story that needs it; see [task-breakdown.md](task-breakdown.md) |
| "Refactor the mailer" | Maintenance with no new behaviour | A task with its own verification, justified by a requirement or risk |
| "Find out whether provider X can schedule sends" | Learning | A spike; see [estimation.md](estimation.md) |
| "Customers see the wrong due date" | Defect | A bug task; do not wrap it in a story |
| "Support SMS reminders" with no user outcome | Feature idea | Ask for the outcome, or list as a non-goal |

Wake's rule on value: a story must matter to the customer or user. Developer concerns are legitimate, but frame them so the customer would see why they matter, or carry them as tasks inside a valuable story.

### INVEST as a working test

Apply this to every story before planning it. A failure usually names the fix.

| Letter | Question | If it fails |
|---|---|---|
| Independent | Can it be scheduled and built in any order, or does it depend on a named story? | Reslice so the dependency is inside one story, or make the order explicit |
| Negotiable | Does it leave room to choose the solution together? | Remove implementation detail; move it to notes |
| Valuable | Would a user notice and care if it shipped alone? | Combine with the work that makes it visible, then reslice vertically |
| Estimable | Can the team roughly size it? | Reduce unknowns: split, or run a time-boxed spike first |
| Small | Does it fit comfortably in one task file with at most 12 plan tasks? | Split using a pattern below |
| Testable | Could you write a test for it today? | Clarify the outcome; if it is a quality target, give it a measure |

Two letters pull against each other. Independent, Negotiable and Valuable are easiest to satisfy for big items; Estimable, Small and Testable are easiest for small ones. Humanizing Work's guidance is to favour I, N and V far from the top of the backlog and E, S and T for what you are about to plan. So do not slice the whole backlog finely; slice what will be planned next.

Wake notes that some dependence cannot be avoided (a first item in a family costs more than later ones). Record it rather than pretend it away.

### Vertical slicing

Think of a feature as a cake with layers (interface, logic, persistence, integration). A vertical slice cuts through every layer and gives the user a small but complete piece. A horizontal slice serves one layer only and has no value on its own.

- Good: "A billing admin can enable one fixed reminder by email." Touches the interface, rule, scheduler, email send and storage, thinly.
- Bad: "Build the reminder database layer." Nothing a user can see; it can look finished and still deliver nothing.
- Never split by role of the implementer (front end, back end, tests, documentation). Testing and documentation are part of finishing each story, in line with the Definition of Done in the Scrum Guide.
- The first slice should reach the edge of the system end to end, even if crude. Later slices widen it.

### Preparing a story before you split it

1. Check the whole story against INVEST, except Small. If it fails Valuable, do not split it; combine it with the work that makes it valuable first. Humanizing Work's reasoning: you cannot slice something with no value into smaller valuable pieces.
2. Name the user, the outcome and the complex part. Words such as "manage", "flexible", "support" and "all" mark hidden variety.
3. List the variations inside that complexity: steps, operations, rules, data kinds, interfaces.

This is the meta-pattern behind every pattern below: find the complexity, list its variations, reduce them to one, deliver that, then expand.

### Splitting patterns

The nine patterns come from Humanizing Work's flowchart (names read from a hosted copy of the poster, so treat the exact labels as unverified against the publisher's guide). Examples use a billing app with invoice reminders.

| Pattern | Signal | Example split |
|---|---|---|
| Workflow steps | Story describes a process with stages | Thin path first: send one fixed reminder end to end; later add admin approval before sending |
| Operations | Verbs like manage, configure, administer | Create a rule; view rules; edit a rule; delete a rule |
| Business rule variations | A domain word hides several rules ("flexible schedule") | One fixed offset after due date; then a repeat every N days; then business-days-only |
| Variations in data | Same behaviour on different kinds of data | Invoices in one currency first; then each additional currency |
| Interface or data entry variations | Same data arrives through several interfaces or a complex interface | Plain numeric field for the offset first; later a calendar-style picker |
| Major effort | The first obvious story is by far the hardest | Support one email provider first; add the second after the integration pattern is proven |
| Simple and complex | A simple core delivers most value | Single reminder for all invoices first; later per-customer overrides |
| Defer performance | Complexity comes from a performance target | Send reminders one by one first; later batch to meet a throughput target |
| Break out a spike | Still baffled after trying the others | Question list plus time-box; the build story follows once the answer is known |

Cohn's SPIDR condenses these into five handles:

| SPIDR | Means | Maps to |
|---|---|---|
| Spike | Research to answer what blocks splitting | Break out a spike |
| Paths | Alternate ways a user can do the thing | Workflow steps, operations |
| Interfaces | Browser, device or simpler versions of the interface | Interface and data entry variations |
| Data | Support a restricted data subset first | Variations in data |
| Rules | Relax a rule temporarily | Business rule variations, defer performance |

Use whichever vocabulary the project already uses.

### Choosing a pattern

Try in this order and stop when one gives a good split:

1. Does the story describe a workflow? Take a thin slice through the whole workflow, or do the first and last steps first and enhance the middle. Workflow splits are easy to get wrong by doing steps one at a time; cut a thin path, not a segment.
2. Does it bundle several operations (manage, configure)? Split by operation.
3. Does it hide several business rules? Deliver one rule, then more.
4. Does it handle several kinds of data, or arrive through several interfaces? Do one first.
5. Is the first story you would pick the hardest one? Group the later stories and defer deciding the order, or reduce the hard part to one narrow case.
6. Is there a simple core with most of the value? Build it first.
7. Does a performance or other quality target drive the complexity? Make it work first, then meet the target in a later story. Keep the quality requirement in the PRD so it is not forgotten.
8. Still stuck? Find the one to three questions holding you back, write a time-boxed spike to answer them, then start again.

### Evaluating a split

Check the result, then adjust.

- Are the new stories roughly equal in size? If one is much larger, split it again.
- Does each satisfy INVEST? Splitting often breaks Independent or Valuable; fix before planning.
- Is there a low-value story you can defer or delete? Every feature has a high-value core and a lower-value tail. A good split exposes the tail as its own story so it can be ranked low or dropped. If your split spreads the tail across all stories, try another pattern.
- Is there an obvious first story that gives early value, learning or risk reduction? If not, reformulate.
- Record deferred stories as non-goals or open questions in `docs/PRD.md` so cutting scope is visible.

Often you will combine patterns: split by operation, then split one large operation by rule.

### How much detail, and when

- The Scrum Guide treats an item as ready when it can be Done within one Sprint, usually reached through ongoing refinement; refinement adds description, order and size. Apply the same idea: add detail to a story only when it is close to planning.
- Keep far-out stories coarse. Detail written early goes stale and invites false precision.
- Do not build a separate "definition of ready" checklist as a gate; use INVEST and the acceptance criteria rules instead.
- If a story still feels unsplittable, it is usually not a real story yet (an architectural component or a task). Rebuild it as a valuable slice first.

### Where stories live in RelayCrew

There is no stories file. Stories appear as:

- Functional requirement rows in `docs/PRD.md`, when the user wants product-level items tracked.
- The Goal and Acceptance criteria of a task file, for work being planned now.

Do not create `docs/STORIES.md` or any new document unasked; that is a scope expansion. The task breakdown for each story is covered in [task-breakdown.md](task-breakdown.md).

## Examples

### Fixing a story that fails INVEST

| Draft | Failure | Revised |
|---|---|---|
| "As a developer, I need a scheduler service so that reminders can run." | Not valuable to a user; names a solution | Remove it as a story. Keep a scheduler task inside "A billing admin can enable one fixed reminder by email" |
| "As a billing admin, I can manage reminders." | Too big, hides four operations | Split by operation; see below |
| "As a billing admin, I want fast reminders." | Not testable | "Reminders are sent within 15 minutes of schedule time" as a non-functional requirement with a verification method |

### Splitting "manage reminders" by operation, then by rule

Original: "As a billing admin, I can manage reminder rules so that overdue invoices are chased."

```
S1  As a billing admin, I can enable one fixed reminder (3 days after due date) for all invoices.   [thin end-to-end first slice]
S2  As a billing admin, I can change the number of days of the fixed reminder.
S3  As a billing admin, I can add further reminders at later offsets (up to 3).
S4  As a billing admin, I can turn reminders off for one customer.
S5  As a billing admin, I can view which reminders were sent.
S6  As a billing admin, I can choose business days only for offsets.            [rule split, lowest value]
```

Evaluation: sizes are close except S1, which carries the scheduler and email integration (major effort). S6 is clearly lowest value and goes to the bottom, so it is recorded as deferred. Each story passes INVEST: S2 depends on S1, which is acceptable and is stated.

### Filled story record for a PRD row

```
FR-3  As a billing admin, I can turn reminders off for one customer, so that a customer in a dispute is not chased. (G2)
Priority: should
Criteria: disabled customer receives nothing on the next run; other customers unaffected; disabling twice is harmless.
Notes: Q1 (partial payments) does not affect this story.
```

### Bad split to good split

| Bad (horizontal) | Good (vertical) |
|---|---|
| Story A: reminder database. Story B: reminder job. Story C: reminder screen. Story D: tests. | S1: fixed reminder end to end. S2: editable offset. S3: multiple offsets. Tests are part of each story. |

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Splitting by layer (database, API, UI) | No slice is demonstrable; integration risk lands last | Cut through all layers for each story |
| Splitting off testing or documentation | Work is reported done before it is verified | Treat both as part of finishing every story |
| Writing "As a developer" stories for technical work | Hides the user value or lack of it | Make it a task inside a valuable story, or justify it by a requirement or risk |
| Splitting a story that fails Valuable | Smaller pieces are equally valueless | Combine with the work that gives value, then reslice |
| Stopping at one split without evaluating it | Unequal sizes and hidden low-value work survive | Check size, INVEST and whether a story can be deferred |
| Over-specifying a story | Removes negotiation and goes stale | Keep the statement short; put detail in criteria and notes near planning time |
| Slicing the whole backlog finely | Detail written too early is wasted | Refine only what will be planned next |
| Treating spikes as stories of value | Hides lack of progress | Time-box them and keep them separate from delivered stories |

## Checklist

- [ ] Each story names a user type that exists in the PRD.
- [ ] Each story states an outcome a user would notice.
- [ ] Each story passes every INVEST question, or the failure is recorded with a fix.
- [ ] No story is defined by a layer or by who implements it.
- [ ] Testing is not listed as a separate story anywhere.
- [ ] Every story fits one task file with at most 12 plan tasks.
- [ ] The first slice reaches the edge of the system end to end.
- [ ] The split was evaluated for equal sizes and for stories to defer.
- [ ] Deferred stories appear as non-goals or open questions in the PRD.
- [ ] Every story links to requirement IDs and a goal.
- [ ] Acceptance criteria for each story follow `requirements-engineering`, including an error or edge case.

## Verify with context7 and gh_grep

- **context7:** only when a story's feasibility depends on a library or service capability. Query the exact version in the manifest: "does `<library>` `<version>` support `<capability>` natively", "`<service>` limits on scheduled or batched operations". Pure slicing of known behaviour needs no query; say so in the report.
- **gh_grep:** to see how maintained projects word and split stories, search the literal line `As a ` inside files named `PRD.md` or under `docs/`, and search the literal heading `## User stories`. Use results to calibrate granularity, not as text to copy.

## Sources

- INVEST in Good Stories, and SMART Tasks, Bill Wake, XP123, 2003: https://xp123.com/invest-in-good-stories-and-smart-tasks/
- How to Split a User Story (episode 175, walkthrough of the Humanizing Work story splitting flowchart), The Humanizing Work Show, 2025: https://the-humanizing-work-show.castos.com/episodes/175-how-to-split-a-user-story
- SPIDR: Five Simple but Powerful Ways to Split User Stories, Mike Cohn, Mountain Goat Software, updated 2026: https://www.mountaingoatsoftware.com/agile/five-simple-but-powerful-ways-to-split-user-stories
- The 2020 Scrum Guide (Product Backlog refinement, Definition of Done): https://scrumguides.org/scrum-guide.html
