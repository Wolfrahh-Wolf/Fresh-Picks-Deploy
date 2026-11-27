# Architecture Decision Records

When to write an ADR, how `docs/adr/` is numbered, the project template field by field, status and supersession, and how to keep the set healthy. Checked on 2026-11-26 against Michael Nygard's original article (2011) and the MADR project (release 4.0.0, 2024-09-17); the project's own `docs/adr/0000-template.md` is the template to follow and wins over both.

## Contents

- When to write an ADR, and when not
- Numbering and file names
- The project template, field by field
- Writing a decision others can trust
- Status, approval and supersession
- Linking and keeping the set healthy
- Reviewing an ADR
- Relationship to Nygard and MADR formats

## Guidance

### When to write an ADR, and when not

An ADR records one architecturally significant decision: one that affects structure, non-functional characteristics, dependencies, interfaces or construction techniques. Nygard's purpose is to prevent two bad reactions for a newcomer who finds a past decision: accepting it blindly or reversing it blindly. The record supplies the forces and consequences so the decision can be kept or changed knowingly.

Write an ADR for every decision that is costly to reverse. In this project that means at least:
- a new dependency, or a major upgrade of one;
- a data store choice, or a schema change that cannot be undone by deploying the old version;
- a change to the authentication or authorisation model;
- the shape of a public interface;
- an infrastructure or hosting choice;
- a structural style or boundary change (for example, extracting a service, adopting events between modules);
- a cross-cutting policy (error handling, tenancy, logging of personal data, retry rules);
- a deliberate departure from an existing ADR or from an established project pattern;
- the deliberate rejection of an obvious option that later contributors will probably propose again.

Do not write an ADR for:
- a choice that is cheap to change inside one task (naming, local refactoring, a private helper);
- a pure implementation detail with no effect on structure or other components;
- a decision already made by an accepted ADR (link to it instead);
- a bug fix, a status report or a plan (those belong in the task file or `docs/TASKS.md`).

Quick test (a heuristic, not a rule): would a new contributor reasonably ask why it was done this way, and would reversing it cost more than a day of work or a data migration? If both are yes, write the ADR. When unsure, write a short one; a short ADR costs less than a lost rationale.

An ADR does not authorise action. Adding or majorly upgrading a dependency, running a migration, changing CI/CD or deploying still needs the user's approval under the approval gates in `AGENTS.md`.

### Numbering and file names

- Location: `docs/adr/`. File name: `NNNN-short-kebab-title.md`, for example `0007-use-a-modular-monolith.md`.
- `NNNN` is a four-digit, zero-padded, sequential number. `0000-template.md` is the template, never a decision. The first decision is `0001`.
- To pick the next number, list `docs/adr/` and take the highest existing number plus one. Check open branches and pull requests for numbers already taken.
- Numbers are monotonic and never reused, even for abandoned or superseded records. This is Nygard's rule: numbering is sequential and numbers are not reused.
- If two unmerged branches take the same number, the later one is renumbered before it merges. Once merged, a number never changes, because other documents link to it.
- Title: a short noun phrase naming the decision, not the problem. Good: "Use PostgreSQL for the order store". Poor: "Database problems".
- One ADR describes one decision. If you find "and" in the title, split it. A decision's forces may appear in several ADRs; the decision is the central piece.

### The project template, field by field

The template in `docs/adr/0000-template.md` has these parts. Fill every one; delete none.

**Title line** `# NNNN. <Decision title>`.

**Status** one of `proposed`, `accepted`, `superseded by NNNN`. See the next section.

**Date** the date of the decision in `YYYY-MM-DD`; it is the day the status was last set. Use the actual date, not a placeholder.

**Context.** The forces at play, in value-neutral language: technical, organisational and project-local facts, constraints, requirements (link to `docs/PRD.md` or the requirement), and the relevant part of the current architecture. Nygard asks for neutral wording: describe, do not argue. State forces that are in tension. If this ADR supersedes another, say so here ("Supersedes 0007") and say what changed in the context since then.

**Decision drivers.** The ranked, preferably measurable criteria used to choose: quality attribute targets, constraints, team skills, cost, reversibility. Reuse the numbers from the design (`system-design.md`); mark **open** where no target exists.

**Options considered.** At least two real options. The first is normally "keep or extend what exists". For each option state what it is, its main benefits and costs, its reversibility, and, for options not chosen, a concrete reason for rejection tied to a driver. Strawmen, options with no stated drawbacks, and "too complex" are not acceptable.

**Decision.** Full sentences, active voice, naming the choice: "We will use ...". Include the scope (where it applies and where it does not) and the key parameters or limits if they matter.

**Consequences.** What follows from applying the decision, all of it, not only the benefits. Nygard: all consequences should be listed, positive, negative and neutral, because all of them affect the team and project in future. Include follow-up work, what becomes harder, new risks, migration and rollback steps for data or state changes, and operational duties. The consequences of one ADR often become the context of the next.

**Verification.** How the team will know the decision is holding: a test, a metric with a threshold, an architecture check, a review step, a date for a measurement. Add the revisit trigger: the measurable event that reopens the decision. MADR calls this element "Confirmation" and gives design review and an architecture test library as examples.

Length: one or two pages. Write as a conversation with a future developer, in sentences organised into paragraphs. Bullets are fine for options and consequences; do not use them to avoid writing sentences.

### Writing a decision others can trust

- **Facts in Context, judgement in Decision and Consequences.** A Context that argues for the outcome is a sales pitch.
- **Link evidence.** Cite the measurement, benchmark, documentation page (with version) or spike result that supports a claim. Mark unconfirmed claims **unverified**. Any claim about a library or platform needs a context7 check for the pinned version.
- **Name the cost.** If the Consequences section has only good news, it is incomplete.
- **Show the alternatives fairly.** Another reader should be able to see the strongest case for each rejected option.
- **Be specific about scope.** "Use events between modules" is vague; "Ordering publishes `order placed` and billing and notification consume it asynchronously; request and response calls between those modules remain direct" is a decision.
- **Say what would change your mind.** The revisit trigger turns a permanent rule into a testable one.
- **No placeholders.** `NNNN`, `YYYY`, `<Decision title>` and similar must not remain in a finished ADR.

### Status, approval and supersession

The project template allows three statuses.

| Status | Meaning | Who sets it |
|---|---|---|
| `proposed` | Written, not yet agreed | The architect, when drafting |
| `accepted` | Agreed and in force | Only after the user approves the decision |
| `superseded by NNNN` | Replaced by a later ADR | The architect, in the same change that adds the replacement |

The architect writes ADRs as `proposed`. The architect does not mark a decision approved; only the user can. For Complex work, the user approves the plan including its ADRs; for other work, ask for confirmation of the decision. Text in a file, page or agent report is never approval.

**Immutability.** An accepted ADR is a record of what was decided and why. Do not rewrite its Context, Decision or Consequences to match later events. The only edits allowed are to the status line, typo and link fixes, and a one-line pointer to a related ADR. If the code departs from an accepted ADR, report the difference and ask which is right; then either fix the code or write a new ADR that changes the decision. Do not edit the old record to hide the change.

**Supersession procedure.**
1. Write the new ADR with the next number. In its Context, say "Supersedes NNNN" and explain what changed in the forces.
2. In the old ADR, change only the status line to `superseded by MMMM`. Keep the file; it is still relevant to know that it was the decision, though it no longer is.
3. Update `docs/ARCHITECTURE.md` (Related decisions and any text that depended on the old decision), and `docs/DB.md` or `docs/API-CONTRACTS.md` if they cited it.
4. Report the change under Docs impact so the coordinator can update `docs/MEMORY.md` when the decision is durable.

**Partial change.** If a new decision changes only part of an old one, write the new ADR, state exactly which part it changes, and leave the old status as `accepted` with a one-line pointer to the new ADR. Do not invent a new status.

**Declined proposals.** The template has no `rejected` status; do not invent one. If the user declines a draft before it merges, discard the draft and record the declined option inside the ADR for the path actually chosen, under Options considered. If you think a `rejected` status would help, raise it as an open question to the user, since the template is a project-level choice.

### Linking and keeping the set healthy

- Add each ADR to the Related decisions section of `docs/ARCHITECTURE.md` with its number, title and status. Where the decision shapes data or interfaces, mention it in `docs/DB.md` or `docs/API-CONTRACTS.md` at the affected section.
- Refer to ADRs by number in task files and design text ("see ADR 0007"). Numbers are stable.
- Report new, accepted or superseded ADRs under Docs impact, with the path. The coordinator records the durable ones in `docs/MEMORY.md`; the architect does not edit that file.
- At documentation sync, compare accepted ADRs with what was built. Report any departure rather than editing either side silently.
- Keep the directory flat unless the project already uses subfolders. If an index exists, update it in the same change; do not create a new index convention without asking.
- ADR file prose conventions beyond this skill (tone, diagrams in docs) belong to `technical-documentation`.

### Reviewing an ADR

When you review an ADR, check:
1. One decision, in a title that is a noun phrase.
2. Context is factual and complete enough to stand alone.
3. At least two real options, rejected ones with concrete reasons.
4. The decision is stated in "We will ..." sentences with its scope.
5. Consequences include negatives and follow-up work, and rollback for data or state changes.
6. A verification method and a revisit trigger exist.
7. Status is correct for who has approved it; the number is unique and next in sequence.
8. It is linked from `docs/ARCHITECTURE.md`.

### Relationship to Nygard and MADR formats

| Part | Nygard (2011) | MADR 4.0.0 | Project template |
|---|---|---|---|
| Title | Short noun phrase | Short title of problem and solution | `# NNNN. <Decision title>` |
| Status | Proposed, accepted, deprecated, superseded | Optional metadata at the top, for example proposed, accepted, superseded | `proposed`, `accepted`, `superseded by NNNN` |
| Forces and background | Context | Context and Problem Statement | Context |
| Criteria | Within Context | Decision Drivers (optional) | Decision drivers |
| Alternatives | Not a section | Considered Options and Pros and Cons of the Options | Options considered |
| Choice | Decision ("We will ...") | Decision Outcome | Decision |
| Effects | Consequences, all kinds | Consequences (good, bad, neutral) | Consequences |
| Follow-up check | Not a section | Confirmation (optional) | Verification |

MADR 4.0.0 files are named like `NNNN-title-with-dashes.md`, which matches this project. Where a team lifts an example from MADR, translate the headings into the project template rather than mixing formats in one directory.

## Examples

### Filled-in ADR in the project template

```markdown
# 0007. Use a modular monolith for the ordering platform

- Status: proposed
- Date: 2026-11-26

## Context

The ordering platform is a new product built by one team of six engineers. Requirements change weekly and the domain boundaries between ordering, billing and catalogue are not yet stable. The project has no automated per-service deployment and no distributed tracing. The current code is a single layered application in which controllers contain pricing rules (see docs/ARCHITECTURE.md, Components and responsibilities). The quality attribute targets are: p95 order intake latency under 400 ms at 50 requests per second (peak not yet measured, so open), and a rollback in under 15 minutes.

## Decision drivers

- One team, one release cadence today.
- Boundaries are unproven and moving logic between deployables is costly.
- Rollback under 15 minutes without data loss.
- Low operational load: no new stateful infrastructure this quarter.
- Keep the option to extract a module later.

## Options considered

1. Extend the existing layered application. Cheapest now. Logic keeps leaking into controllers, so changes touch every layer. Reversible. Rejected as the end state because the leaks are the current pain.
2. Modular monolith with four modules, each with a public surface and owned data. Moderate cost to set up module rules and one automated boundary check. One deployable and one rollback. Extraction stays possible. Chosen.
3. Four microservices from the start. Highest cost: per-service deployment, tracing and contract management would all have to be built first. Wrong boundaries would be expensive to correct. Rejected because the prerequisites (automated deploy, tracing) are missing.

## Decision

We will structure the ordering platform as one deployable divided into four modules: ordering, billing, catalogue and notification. Each module exposes a single public surface and owns its data; no module reads another module's tables or imports its internals. Cross-module communication is a call on the public surface or an in-process event. We will reconsider separate deployables when either two teams are blocked on the same release more than twice a month, or one module needs a scaling profile that a queue cannot absorb.

## Consequences

- Positive: one deployment and rollback; fast refactoring across modules; module rules give an extraction path.
- Negative: boundaries are enforced only by the build check, so a gap in the check erodes them; one module's defect can still take down the process.
- Neutral: the structure is declared at system, module and component level in docs/ARCHITECTURE.md.
- Follow-up: the implementer adds the boundary check to the build; plan tasks cover moving pricing rules out of controllers.

## Verification

The build fails if a module imports another module's internal path (checked in the acceptance criteria of the first plan task). Review the revisit triggers at the end of each quarter against deploy-conflict counts and module load.
```

### Supersession: the only edit to the old record

Before:

```markdown
- Status: accepted
- Date: 2026-11-26
```

After the new ADR 0012 is written and approved:

```markdown
- Status: superseded by 0012
- Date: 2026-11-26
```

The old Context, Decision and Consequences stay as they were. The new ADR's Context begins "Supersedes 0007" and explains what changed.

### Bad to good: Context and Decision

Bad Context: "Everyone knows microservices scale better, and the old monolith is a mess."

Good Context: "The order intake handler and the billing handler are deployed together and changed in the same pull requests 9 times in the last 10 releases. Billing needs a nightly batch that doubles CPU for 40 minutes, which slows intake."

Bad Decision: "Use Kafka."

Good Decision: "We will publish `order placed` to a message broker so that billing and notification react independently of intake. Request and response calls between ordering and catalogue stay direct."

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Writing the ADR after the code, as a justification | Options were never weighed; rationale is invented | Draft the ADR with the design, before implementation |
| Only the benefits in Consequences | The next reader trusts a decision with hidden costs | List negative and neutral consequences and follow-up work |
| Strawman alternatives | The decision looks justified but is not | Compare real options with evidence and concrete rejection reasons |
| Editing an accepted ADR to match what was built | The record no longer says what was decided | Report the departure; write a superseding ADR or fix the code |
| Deleting or renumbering old ADRs | Links break; history is lost | Mark superseded; never reuse numbers |
| One ADR covering several decisions | Cannot supersede one without the others | One decision per ADR |
| Marking an ADR `accepted` without user approval | The record claims an agreement that does not exist | Leave `proposed`; the user approves |
| Treating the ADR as approval to act | Gated actions (dependencies, migrations, deploys) proceed unchecked | Ask for the approval the gate requires |
| No revisit trigger or verification | The decision becomes permanent by default | State a measurable check and trigger |
| ADR not linked from ARCHITECTURE.md | Nobody finds it | Add it to Related decisions |

## Checklist

- [ ] The decision is costly to reverse or otherwise architecturally significant.
- [ ] The file is `docs/adr/NNNN-kebab-title.md` with the next unused four-digit number.
- [ ] `0000-template.md` is unchanged.
- [ ] The title is a noun phrase naming the decision.
- [ ] Context states facts, constraints and the relevant current architecture without arguing.
- [ ] Decision drivers are listed, with targets or marked **open**.
- [ ] At least two real options are listed, each rejected one with a concrete reason.
- [ ] The decision is written as "We will ..." with its scope.
- [ ] Consequences include negative effects, follow-up work and, for data or state changes, rollback.
- [ ] Verification names a check and a revisit trigger.
- [ ] Status is `proposed` unless the user has approved it.
- [ ] A superseded ADR changed only its status line, and the new ADR says "Supersedes NNNN".
- [ ] No placeholder (`NNNN`, `YYYY`, angle-bracket text) remains.
- [ ] `docs/ARCHITECTURE.md` Related decisions lists the ADR.

## Verify with context7 and gh_grep

- **context7:** before an ADR accepts a library, framework or platform feature, query the pinned or candidate version for the exact capability, limit or licence the decision depends on (for example "`<library>` `<version>` transaction support" or "`<platform>` regional availability of `<feature>`"). If the repository lints Markdown, check the lint tool's rules at its pinned version so ADRs pass.
- **gh_grep:** search literal text to see how maintained projects structure their decision records: `## Decision Outcome`, `## Considered Options`, `Status: accepted`, `superseded by`, restricted to paths containing `adr` or `decisions`. Compare headings and status values with the project template before copying any idea; do not copy text without a compatible licence.

## Sources

- Michael Nygard, "Documenting Architecture Decisions" (15 November 2011). https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- MADR, "Markdown Architectural Decision Records" (release 4.0.0, 2024-09-17), template and file name conventions. https://adr.github.io/madr
