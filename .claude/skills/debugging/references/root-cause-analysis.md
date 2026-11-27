# Root Cause Analysis

How to build and prove a causal chain from trigger to symptom, where five whys helps and where it fails, and how to separate trigger, root cause and contributing factors with a stated confidence; technique-level guidance that does not depend on a library version, checked 2026-11-26.

## Contents

- Definitions: trigger, root cause, contributing factor
- Building the causal chain
- Five whys: use and limits
- Proving the cause
- The symptom coverage table
- Confidence levels
- When the cause is a design flaw
- Writing the conclusion

## Guidance

### Definitions: trigger, root cause, contributing factor

Use these three terms in every conclusion and keep them apart.

| Term | Definition | Test | Typical form |
|---|---|---|---|
| **Trigger** | The event or input that made the failure appear on this occasion | Without it, the failure would not have happened **now**, but the defect would still be there | A deploy, a particular request, a date rollover, a slow dependency, a dependency upgrade |
| **Root cause** | The defect or missing condition in the system, within the team's control, whose correction prevents this class of failure from recurring | If you correct it and replay the trigger, the failure does not occur | A wrong assumption in code, a missing validation, a mismatched key, an unguarded shared state, a lost invariant |
| **Contributing factor** | A condition that made the failure more likely, harder to detect or more damaging, but is neither the trigger nor sufficient alone | Removing it reduces likelihood or impact but the defect remains | Missing test coverage, a misleading log message, a timeout that is too long, a config default |

How they relate: the root cause is a latent defect; the trigger is what exposes it; contributing factors explain why it was not caught earlier, why it was bad, or why it took long to find. A report that names only the trigger invites a patch that suppresses it ("do not run on the 31st") while the defect remains.

Two counterfactual questions separate them:

1. **If I correct X and replay the same trigger, does the failure stop?** If yes, X is the root cause (or the root cause is upstream of X; keep asking).
2. **If I prevent the trigger but leave X, can the failure still occur by another route?** If yes, X is the root cause and the trigger was one of several routes.

Contributing factors fail question 1 (correcting them alone does not stop the failure) but change likelihood or impact.

Use blameless language: describe the system and the information available, not the person. A person "made an error" only as a prompt to ask why the system allowed or invited it. This follows the approach in the Google SRE book chapter on postmortem culture: assume everyone acted with good intentions and the information they had, and look for contributing causes rather than someone to blame.

### Building the causal chain

A causal chain links the root cause to the symptom through the intermediate states. Every link is a claim with evidence.

```text
Root cause -> mechanism -> intermediate state -> ... -> symptom
```

Build it backwards from the symptom, and verify each link forwards.

1. **Start at the observed symptom** (the verbatim error or the wrong value) and the exact place it surfaced.
2. **Ask what state made that happen.** Name the variable, record or resource and its wrong value. Evidence: a log line, a captured value, a stack frame.
3. **Ask where that state was produced.** Find the **first** place the value became wrong (see fault isolation). The error site is rarely the cause site.
4. **Ask why the producer behaved that way.** Name the line of code, the configuration or the data. Evidence: reading the code and demonstrating the behaviour.
5. **Stop at a cause that is actionable**: a thing the team can change which removes the failure class. Stop before you reach "people did not think of it" or "the technology is complex", which cannot be fixed.
6. **Check forward.** Walking from the root cause to the symptom, does each link follow with the evidence you hold? Any link you cannot evidence is a hypothesis; label it as one.

Mark each link with its evidence class:

| Class | Meaning | Example |
|---|---|---|
| Observed | You saw it directly | The captured request body contains `null` at that field |
| Demonstrated | You made it happen with an experiment | Injecting the condition produced the same error text |
| Inferred | Follows from observed facts by reasoning | Code path analysis shows this branch is the only writer |
| Assumed | Believed, not checked | The library behaves as documented in this version |

A chain with an assumed link is not proven. Either check the assumption or lower the confidence and say which link is assumed.

### Five whys: use and limits

Asking why repeatedly is a good habit, and "five" is a rule of thumb, not a requirement or a stopping rule. It helps you move from the symptom toward a cause. It fails in predictable ways, so use it as a way to generate links for the chain and never as the proof.

| Limit | What goes wrong | Counter |
|---|---|---|
| It is linear | Real failures have several causes; one chain drops the others | Branch where a why has more than one answer; keep each branch |
| Answers are opinion | Each why is only as good as the person's guess | Require evidence at every step; an unevidenced step is a hypothesis |
| It stops early | The questioner stops at the first comfortable answer, often a person or a missing test | Continue until the cause is actionable in the system and passes the counterfactual test |
| It stops at people | "Developer forgot" ends the inquiry and blames | Ask what let the mistake reach production: review, tests, types, defaults |
| It runs past the evidence | A fifth why drifts to generalities ("process is weak") | Stop at the deepest link you can evidence |
| Depends on the asker | Two people get two chains | Test the chain with the counterfactual, not with agreement |
| Mistakes correlation for cause | Adjacent events look causal | Demonstrate with removal or injection |
| Skips the trigger | Explains the defect but not why now | Add a separate answer for why it appeared at this time |

How to use it well: do the whys, then convert the chain into the symptom coverage table below and test the root cause with a counterfactual. If any why in your chain would be a different answer in a second environment, it is probably a contributing factor, not the cause.

A short, well-formed chain:

```text
Symptom:   Nightly export has duplicate rows.
Why 1:     The same order is inserted twice.      (observed: two rows, same order_id, 40 ms apart)
Why 2:     The job runs twice at 02:00.           (observed: two start lines in the log)
Why 3:     Two scheduler instances are running.   (observed: two processes after a deploy)
Why 4:     The insert has no uniqueness guard.    (observed: no unique index on order_id; code path inspected)
Stop:      Why 3 is the trigger; why 4 is the defect that lets any duplicate run corrupt data.
```

### Proving the cause

A cause is proven when an experiment, not only reasoning, ties it to the failure. Use at least one of these, strongest first.

| Method | Procedure | Strength |
|---|---|---|
| **Counterfactual removal** | In a disposable copy, change only the suspected cause and replay the exact reproduction. The failure disappears | Strongest; show the command and output before and after |
| **Injection** | In a clean setup without the failure, introduce only the suspected condition. The same failure appears with the same message | Strong; also proves the condition is sufficient |
| **Prediction test** | Derive a consequence of the cause that you have not yet seen (another input that should fail, another value that should be wrong) and check it. It fails as predicted | Strong when removal is impractical |
| **Revert the change** | Revert the commit found by bisect in a scratch copy; the failure disappears | Strong for regressions; shows the commit matters, not that its content is the cause |
| **Elimination** | Every alternative hypothesis is disproven | Weakest; valid only if the list is exhaustive, which you cannot usually show |

Rules:

- A passing run after a change proves nothing for an intermittent failure unless it is repeated enough (see [bug-reproduction.md](bug-reproduction.md) for the run count).
- Do the experiment in a disposable copy outside the project tree. You do not edit the project.
- Prove both directions where you can: removal makes it stop, injection makes it start.
- Compare the failure after your experiment with the original: same message, same location. A different failure means you changed something else.
- The experiment must change one thing. A "fix" that also tidies other code proves nothing about which part mattered.

If you can only show correlation (the failure and a condition co-occur) say so and cap confidence at Medium or lower.

### The symptom coverage table

The cause must explain **every** observed symptom. Write the table; an empty "explained by" cell means the cause is not proven.

| Symptom | Observed evidence | Explained by the cause? | How |
|---|---|---|---|
| S1 | <verbatim error or value> | yes / no / partly | <mechanism> |

If a symptom is not explained: either there is a second cause or yours is incomplete. Return to hypotheses. Common cases: one cause explains the crash but not the earlier wrong value; one cause explains the failure in CI but not locally; one cause explains the rate but not the first occurrence date.

### Confidence levels

State one level and the reason. Use these definitions, which match the debugger's definition of done.

| Level | Meaning | Required |
|---|---|---|
| **High** | Cause proven; all symptoms explained | A removal or injection result; the coverage table fully filled; every hypothesis dispositioned |
| **Medium** | Cause strongly supported but one aspect is circumstantial | Say which aspect and why it is not shown (for example intermittent, so the removal result is statistical) |
| **Low** | Best available hypothesis; gaps remain | List the gaps and the next experiment or access needed; the status in the report should say so |

Never write "likely" without a level. Never claim High with an assumed link in the chain.

### When the cause is a design flaw

Some causes are not local defects: a missing abstraction, a data model that cannot represent a case, a boundary in the wrong place, an architecture that cannot be made safe by a patch. Signs: the correct fix would touch many unrelated places, the same defect keeps recurring in different spots, or two requirements cannot both hold.

- Report the cause and the evidence anyway.
- Propose the smallest safe mitigation, labelled as a mitigation, not a fix, and say what it leaves open.
- Escalate: the design change belongs to the architect and needs user approval. For architecture decisions, load `system-architecture`. Do not design the replacement yourself.

### Writing the conclusion

Use this shape in the report. It is short enough to read in a minute and complete enough to verify.

```text
Root cause (<High|Medium|Low>): <one sentence naming component and mechanism>
Trigger: <what made it appear this time>
Contributing factors: <list; each with how it increased likelihood or impact>
Chain: <symptom> <- <state> <- <state> <- <root cause>, each with evidence class
Proof: <removal/injection/prediction result, with command and output>
Not explained: <symptoms or aspects left open, or "none">
```

## Examples

### Filled-in conclusion

Brief: invoices are generated twice for some customers on the first day of a month.

```text
Root cause (High): invoice_job.generate() derives the billing period from the host's local
  date, but the scheduler passes a UTC timestamp near midnight, so for hosts in UTC+1 the
  "previous month" is computed twice (once on the last day, once on the first).
Trigger: the scheduler was moved to a host in Europe/Berlin on 2026-10-04 (deploy a3f9c01).
Contributing factors:
  - No unique constraint on (customer_id, period) in the invoices table (duplicates accepted).
  - Tests ran with TZ=UTC, so the local-date path was never exercised.
  - The log line "generated invoice" omits the period, hiding the duplicate for 6 weeks.
Chain: duplicate invoice rows (observed) <- job ran for two different periods for one
  customer (observed in log, periods 2026-09 and 2026-10 on 2026-10-01 00:20 UTC+1)
  <- period computed from local date (code read: invoice_job.py:41) <- host timezone differs
  from UTC (observed: TZ=Europe/Berlin).
Proof: in a scratch copy, forcing the period computation to UTC and replaying the captured
  trigger timestamp produced 1 invoice; unmodified code produced 2 (3 of 3 runs each).
  Injection: TZ=Europe/Berlin on a clean UTC setup reproduced the duplicate (3 of 3).
Not explained: none. Symptom table: S1 duplicate rows - yes; S2 only on the first of the
  month - yes (only date boundary at midnight crosses a month); S3 started in October - yes.
```

### Five whys that stopped too early

Bad:

```text
Why? The deploy broke login.   Why? A developer changed the config.   Why? He did not test.   Stop.
```

Good (branching, evidence at each link, actionable stop):

```text
Why did login return 500?            Session store key was undefined (observed, log line).
Why undefined?                       Config key renamed from SESSION_URL to STORE_URL (diff).
Why did the rename reach production? Two branches: (a) no startup check for required keys (code read);
                                     (b) the test config still defined the old key, so tests passed (diff of test config).
Root cause: configuration is read lazily with no validation.   Contributing: (b).
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reporting the trigger as the cause | The patch suppresses the trigger and the defect persists | State trigger, root cause and contributing factors separately |
| Stopping at "human error" | Not actionable; blames a person | Ask what let the error through and fix that |
| Treating five whys as proof | Whys are guesses without evidence | Use whys to build the chain, then prove it with removal or injection |
| Claiming High confidence with an assumed link | The assumption may be wrong | Check the assumption, or lower the level and name it |
| Leaving a symptom unexplained | A second cause remains | Fill the coverage table; return to hypotheses on any gap |
| A "fix" that also changes unrelated code | The experiment proves nothing | Change one thing in a disposable copy and replay |
| Accepting a post-hoc correlation | Two things co-occurred, not caused | Demonstrate in both directions where possible |
| Calling a design flaw a bug and proposing a local patch | The failure class recurs | Escalate with a mitigation clearly labelled |
| Naming a person in the conclusion | Discourages reporting and teaches nothing | Describe the system and the information available |
| Writing "likely" with no level | The reader cannot decide how much to trust it | State High, Medium or Low with the reason |

## Checklist

- [ ] The conclusion names trigger, root cause and contributing factors separately.
- [ ] Every link in the causal chain has an evidence class, and no link is only assumed.
- [ ] The cause was proven by removal, injection or a confirmed prediction, with command and output recorded.
- [ ] The proof experiment changed exactly one thing in a disposable copy outside the project.
- [ ] The post-experiment failure matches the original in message and location.
- [ ] Every symptom in the brief appears in the coverage table and is explained.
- [ ] Each hypothesis has a disposition with evidence.
- [ ] Confidence is stated as High, Medium or Low with the reason.
- [ ] For an intermittent failure, the result states runs and outcomes.
- [ ] The language is blameless and names no individual.
- [ ] A design-level cause is escalated rather than patched silently.

## Verify with context7 and gh_grep

- **context7:** When the chain depends on library, framework or runtime behaviour, confirm the documented behaviour at the **locked** version before treating it as a link: for example how the library handles a null argument, its default timeout, its transaction or caching semantics, and any changelog entry or known issue that matches the symptom. Query form: "`<library>` `<version>` `<behaviour>`" and "`<library>` `<version>` known issues `<symptom>`".
- **gh_grep:** Search the verbatim error and a distinctive fragment of the failing code pattern to see whether maintained projects hit the same cause, for example the exact exception text, or the literal call shape such as `register('jwt'` for a key mismatch pattern. Use the result to form a hypothesis, then prove it here.

## Sources

- Google SRE book, chapter 15, Postmortem Culture: Learning from Failure: https://sre.google/sre-book/postmortem-culture/
- git-bisect manual, for locating a trigger commit (Git 2.56.0): https://git-scm.com/docs/git-bisect.html
- Jest CLI options (Jest 30.5), for repeating tests when proving an intermittent cause: https://jestjs.io/docs/cli
