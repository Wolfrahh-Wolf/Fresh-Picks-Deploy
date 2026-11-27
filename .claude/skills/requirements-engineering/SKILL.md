---
name: requirements-engineering
description: "Use when eliciting, writing or checking requirements: functional and non-functional needs, constraints, ambiguity and testable acceptance criteria."
---

# Requirements Engineering

Turn a vague request into unambiguous, testable, traceable requirements and observable acceptance criteria. The architect uses this skill to decide what must be true before anyone decides how to build it.

## When to use

- The request contains vague words ("fast", "easy", "secure", "like the old one") or no success measure.
- A change needs functional requirements, non-functional targets or constraints written down.
- Acceptance criteria are missing, cover only the happy path, or cannot be checked by someone else.
- Two statements in the request, the docs or the code seem to contradict each other.
- You are reviewing existing requirements in `docs/PRD.md` or a task file for testability.
- Assumptions, open questions or stakeholders need to be made explicit before design starts.

## Do not use for

- PRD structure, user stories, task breakdown, estimates: load `product-technical-planning`.
- Solution design, component boundaries, architecture decisions: load `system-architecture`.
- Choosing a technology or testing feasibility: load `technical-research`.
- Writing or running the tests that prove the criteria: load `testing-strategy` or `test-driven-development`.
- Threat modelling or security control design: load `security-engineering`.

## Research: context7 and gh_grep

- You MUST consult **context7** before writing a requirement or criterion that depends on a library, framework, SDK, CLI tool, cloud API or platform standard, for example a rate limit, a supported browser or runtime version, a token lifetime or a WCAG level. Check the project's manifest or lockfile first and query that version. Useful queries: `<library> <version> default timeout`, `<service> API rate limits per minute`, `<framework> <version> supported Node.js versions`, `WCAG 2.2 success criteria contrast minimum`.
- You MUST search **gh_grep** when you are unsure how a behaviour is normally specified or tested in practice, for example a pagination edge case, a retry rule or an error-response shape. Search literal code, not descriptions. Useful searches: `Scenario Outline:`, `Then the response status is 429`, `Retry-After`, `shall not exceed`, `Feature: .* password reset`.
- Neither is needed for pure project-internal rules, such as a business rule taken from `docs/PRD.md` or a stakeholder answer. Say so in the report.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/requirement-elicitation.md](references/requirement-elicitation.md) | The request is vague, stakeholders are unclear, assumptions need surfacing, wording is ambiguous, or two requirements conflict. |
| [references/functional-nonfunctional-requirements.md](references/functional-nonfunctional-requirements.md) | You must classify a statement, write a requirement sentence, or give a quality attribute a measurable target and verification method. |
| [references/acceptance-criteria.md](references/acceptance-criteria.md) | You are writing or checking criteria, Given/When/Then scenarios, edge and negative cases, or deciding whether a requirement is done. |

## Workflow

The architect is the only agent that loads this skill. The coordinator owns the task file status and records; the architect writes requirements into the owning docs and acceptance criteria into the task file.

1. **Collect what exists.** Read the brief, the task file, `docs/PRD.md`, `docs/MEMORY.md`, related specs and the code the change touches. Resolve every question the repository can answer before asking anyone.
2. **Restate the goal and list unknowns.** Write the goal in one sentence. List stakeholders, vague terms, undefined nouns, missing quantities and unstated assumptions. Open the elicitation reference for the techniques.
3. **Decide what blocks.** A question is blocking if two reasonable answers lead to different observable behaviour. Ask all blocking questions together, numbered, each with a proposed default. For non-blocking gaps, state the assumption and mark it.
4. **Classify each statement.** Label it functional, quality (non-functional), constraint, interface, data or business rule. Split compound statements into single ones. Route design choices to `system-architecture`.
5. **Write each requirement.** One condition, one actor, one response, one ID. Use "shall" for binding statements. Replace every vague word with a number, a unit and a measurement condition, or mark the item **open**.
6. **Give every non-functional requirement** a metric, a target, the conditions it is measured under and a verification method. If the target is unknown, record the metric and mark the target **open** with who can decide.
7. **Write acceptance criteria.** For each functional requirement cover the normal path, at least one error or negative case and the boundary values. Make each criterion observable by someone who did not write it. Reference the requirement ID.
8. **Check the set.** Look for duplicates, contradictions, missing error handling, orphan criteria and requirements with no source. Resolve conflicts from documents first. After 2 failed clarification attempts, escalate with both statements quoted verbatim.
9. **Record in the owning docs.** Put requirements in `docs/PRD.md` (or the doc that owns that topic) and criteria in the task file. Keep assumptions and open questions visible, never buried.
10. **Report.** Return the standard report. Say which requirements are **open**, which assumptions are unconfirmed, and that approval belongs to the user.

### Differences by situation

| Situation | What changes |
|---|---|
| Writing new requirements | Run every step; expect to ask questions. |
| Reviewing existing requirements | Skip step 3 unless a gap is found; report defects with the ID, the quoted text and the rule broken. Do not rewrite silently. |
| Spec and code disagree | Report both and ask which is right. Do not edit either to match. |
| Trivial change | Do not load this skill unless the criteria are genuinely unclear. |

## Standards

- Every requirement has a unique, stable ID that is never reused, even after the requirement is removed.
- Every requirement is singular: one actor, one response, no "and" joining two testable behaviours.
- Binding statements use "shall"; desirable ones use "should" and carry a stated priority. Do not mix other modal verbs.
- No vague term (fast, easy, secure, scalable, robust, user-friendly, appropriate, as needed) appears without a number, a unit and a condition.
- Every non-functional requirement states metric, target, measurement conditions and verification method, or is marked **open**.
- Every requirement has a named verification method: test, inspection, analysis or demonstration.
- Requirements state what the system does or must satisfy, not how it is built. A design or technology constraint is allowed only when labelled as a constraint with its source.
- Every functional requirement has at least one normal, one error or negative, and one boundary criterion, or the missing case is marked **open**.
- Every acceptance criterion is observable at a system boundary (output, response, message, state a user can see) and passes or fails without interpretation.
- Every requirement traces to a source (user statement, doc, law, existing behaviour) and every criterion traces to a requirement ID.
- Assumptions are marked as assumptions, each with how it will be confirmed. Unconfirmed claims are marked **unverified**.
- Missing requirements become numbered open questions. Never invent a requirement the user did not ask for.
- Contradictions are quoted verbatim in the report. Never resolve one by silently picking a side.
- Never mark a requirement approved. Only the user can approve.
- Project conventions and existing `docs/` beat these defaults, except where they are unsafe; then report it.
- No placeholder markers, "to be decided" entries or empty sections remain. Use **open** with an owner instead.

## Verification

- [ ] Search the requirements for vague words and confirm each hit has a number or is marked **open**: `grep -nEiw "fast|quick|easy|simple|secure|scalable|robust|flexible|user-friendly|appropriate|adequate|as needed|etc" docs/PRD.md` (PowerShell: `Select-String -Path docs/PRD.md -Pattern '\b(fast|quick|easy|secure|scalable|robust)\b'`).
- [ ] Check that IDs are unique: `grep -oE "\b(FR|NFR|CON|IF|DR)-[0-9]+" docs/PRD.md | sort | uniq -d` prints nothing for definitions (references are fine).
- [ ] Count requirements without a criterion: list every requirement ID and confirm each appears in the task file's acceptance criteria.
- [ ] Re-read each criterion and answer "who observes this, where, and how?" for it. A blank answer means rewrite.
- [ ] Confirm every non-functional requirement row has metric, target, conditions and method, or **open**.
- [ ] Confirm each conflict and each blocking question is in the report with quotes and a proposed default.
- [ ] Confirm any library, standard or platform fact used was checked with context7 or official documentation, or is marked **unverified**.

## Output

Return the standard report. Add skill-specific content as follows.

- **Evidence:** the searches and checks from Verification with their results, and counts such as "14 requirements, 14 with criteria, 3 targets open".
- **Research:** the context7 and gh_grep queries used and what they confirmed, or "none needed: project-internal rules only".
- **Docs impact:** requirements added or changed in `docs/PRD.md` (owner: architect); interface or data requirements that affect `docs/API-CONTRACTS.md` or `docs/DB.md` (owner: architect); UI behaviour requirements that affect `docs/DESIGN.md` (owner: architect); a decision costly to reverse that needs an entry in `docs/adr/` (owner: architect). The coordinator updates `docs/TASKS.md` and `docs/MEMORY.md`; propose a memory entry when a durable constraint or business rule was learned.
- **Summary additions:** the requirement count by type, the list of **open** items with who can resolve each, the assumptions made, and any conflicts escalated.
- **Open questions:** numbered, each with a proposed default and what changes if the default is wrong.
