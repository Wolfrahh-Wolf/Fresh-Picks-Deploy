# Bug Reproduction

How to turn a reported failure into a minimal, executable, repeatable reproduction, including environment capture and intermittent failures; assumes Git 2.x, Node.js 20 or later, Python 3.10 or later, Jest 30 and pytest 8 behaviour, checked 2026-11-26. The project's own manifest and lockfile win over any version here.

## Contents

- Capture the failure before touching anything
- Capture the environment
- Reproduce with the original steps first
- Reduce to a minimal reproduction
- Intermittent failures
- Reproducing CI-only and UI failures
- The attempt log and when to stop
- Reproduction safety

## Guidance

### Capture the failure before touching anything

Write down four things first, from the brief and from what you observe, in this order:

1. **Expected behaviour** in one sentence a stranger could check.
2. **Actual behaviour**, including every symptom, not only the loudest one. A crash plus a wrong value plus a slow response are three symptoms; the cause must explain all of them.
3. **Verbatim error text**: copy the message, exception class, error code, stack trace and exit status exactly. Do not retype from memory and do not shorten. Keep the first and last frames of a long trace in the report and store the full text in the task notes.
4. **Trigger conditions as reported**: who, which data, which build, which time, what happened immediately before.

Decide up front what "reproduced" means. It is an observable, checkable result: an exit status, an assertion message, an HTTP status and body, a screenshot state. "Looks broken" is not a check.

### Capture the environment

Record the environment in the same text as the reproduction steps, so another agent can rebuild it. Record what you can observe, not what you assume.

| Item | How to capture | Why it matters |
|---|---|---|
| Source revision | `git rev-parse HEAD`, then `git status --short` for uncommitted changes | A failure on a dirty tree is not a failure of a revision |
| Operating system and architecture | `uname -a` on Linux and macOS; the `ver` command or `systeminfo` on Windows | Path, line-ending, case-sensitivity and native-module differences |
| Runtime version | `node --version`, `python --version`, `java -version` | Behaviour changes between runtime releases |
| Dependency versions | Read the lockfile, not the manifest range; `npm ls <package>` or `pip show <package>` for what is installed | A range resolves differently on different days |
| Configuration | Names and non-secret values of environment variables and config files; mark secrets as `<REDACTED>` | The most common cause of "works on my machine" |
| Locale, timezone, clock | `date -u`, `TZ`, `LANG`, `LC_ALL` | Date, sort-order and encoding failures |
| Resources | CPU count, memory limit, disk space, open-file limit (`ulimit -n`) | Failures that only appear under constraints |
| Services and data | Versions of the database or queue, schema revision, seed data identity | Data-dependent failures |
| Command line | The exact command, working directory and arguments | The reproduction is a command, not a story |

Compare the failing environment with your reproduction environment line by line. A mismatch is not a diagnosis; it is the first thing to vary later (see [fault-isolation.md](fault-isolation.md)).

If the project provides a container definition or a documented dev setup, use it. Do not install global tools or change system configuration to make a reproduction work; build the environment in a scratch directory or container and delete it afterwards.

### Reproduce with the original steps first

Run the reported steps exactly, once, before any simplification. Three outcomes:

- **Reproduced:** note the failure rate (one run is "1 of 1"), save the exact command and output, and go to reduction.
- **Not reproduced:** do not conclude the report is wrong. Compare environment and data against the report, then work through the attempt log below.
- **Reproduced differently** (different error, same area): record both. They may be two symptoms of one cause or two separate bugs. Do not merge them until the cause explains both.

For a failing test, run only that test first, with the project's own test command and a name filter. Examples: `jest -t "<test name regex>"` runs tests whose full name matches; `pytest <path>::<test_name>` runs one pytest test. Run the whole file next, then the whole suite. If it passes alone and fails in the suite, the failure depends on other tests: go to the intermittent section.

### Reduce to a minimal reproduction

A minimal reproduction is the smallest program, input and configuration that still shows the same failure. It is the single most useful artefact you can hand the implementer, because it is also the seed of the regression test.

Procedure:

1. Save a copy of the full reproduction and its output as the baseline.
2. Remove one thing: a feature flag, a middleware, a request field, half of the input, a dependency, a line. Re-run.
3. If the **same failure** still appears (same message, same location), keep the removal. If it vanishes or changes, restore the thing: it is relevant. If it changes into a different failure, note it and restore.
4. Repeat until nothing more can be removed without losing the failure. Remove in halves first (cut the input in half, then a quarter) and fall back to single items.
5. Re-run the minimal version 3 times from a clean start to confirm it is stable.
6. Check the minimal version still matches the original failure, not merely a similar one: compare the error text and the failing frame.

What to reduce, in order of cheapness:

| Dimension | Reduction moves |
|---|---|
| Input data | Halve the file or payload; replace real values with the smallest synthetic ones; drop optional fields |
| Steps | Remove steps from the start of the sequence that do not change state used later |
| Code path | Call the failing function directly with the captured arguments |
| Configuration | Reset to defaults one option at a time |
| Dependencies | Replace a service with a stub that returns the captured response |
| Environment | Move from the full stack to a single process, from a container to a local run, or the reverse if it stops failing |

Stop reducing when the next step costs more than it saves. A reproduction of 20 lines that fails every time is enough; do not golf it.

A reduction run is itself a hypothesis test: "removing X does not change the failure" is evidence that X is irrelevant. Record it that way.

### Intermittent failures

An intermittent failure is a deterministic failure whose trigger you have not yet found. Treat randomness as a missing variable, not as a property of the bug.

First measure, then explain. Run the failing command in a loop and count outcomes:

```bash
# Run 50 times, count failures; the command stops reading output, only the exit status matters.
fails=0
for i in $(seq 1 50); do
  <test command> >/dev/null 2>&1 || fails=$((fails+1))
done
echo "failures: $fails of 50"
```

State the result as a rate with the run count. "Sometimes fails" is not a measurement.

Common classes and the first experiment for each:

| Class | Typical sign | First experiment |
|---|---|---|
| Race between threads, tasks or processes | Fails more under load or on more cores | Run serially (Jest `--runInBand`), then with CPU stress; add an artificial delay at the suspected interleaving point in a scratch copy |
| Test order or shared state | Passes alone, fails in the suite; changes with order | Run the failing test alone; run with shuffled order and the printed seed (Jest `--randomize --seed <n>`); bisect the set of preceding tests |
| Timing and timeouts | Fails on slow machines or CI | Measure the duration of the failing step across 50 runs; compare with the limit |
| Time, date, timezone | Fails near midnight, month end, DST change | Fix the clock or run with a different `TZ`; compare behaviour across values |
| Randomness | Differs per run without code change | Print and fix the random seed; replay with the same seed |
| Resource exhaustion or leaks | Fails after many iterations or long uptime | Watch memory, handles and ports across 50 runs; Jest `--detectOpenHandles` lists open handles (it implies `--runInBand` and slows the run, so use it only for diagnosis) |
| External dependency | Fails when a network call is slow or returns different data | Replace the call with a recorded response and re-run |
| Environment drift | Fails on one machine or runner only | Diff the environment table above between a failing and a passing machine |
| Uninitialised or reused data | Different data per run | Log the input identity per run (not the content) and correlate with failures |

Techniques that make the failure more likely, so you can observe it:

- **Remove nondeterminism you control:** fix seeds, fix the clock, serialise execution, pin the data. If the failure disappears, the removed variable is implicated; restore variables one at a time.
- **Amplify:** repeat the operation many times, run several copies in parallel, restrict CPU or memory, add latency to the dependency. Do this on a local or test environment only.
- **Capture on failure:** run the loop with output saved per run and keep only the failing runs. Compare a failing run's log with a passing run's log, line by line, from the start.
- **Hangs:** for Python, `faulthandler.dump_traceback_later(<seconds>, repeat=True)` dumps every thread's traceback if the program is still running after the timeout; pytest can do this per test with the `faulthandler_timeout` option. For Node, the inspector or a process signal can show where it is stuck (see [logging-tracing.md](logging-tracing.md)).
- **Crashes with no Python traceback:** `python -X faulthandler` (or the `PYTHONFAULTHANDLER` environment variable) dumps the Python traceback on fatal signals such as SIGSEGV; Python's development mode (`python -X dev`) additionally enables extra runtime checks, resource warnings and asyncio debug output. It is slower; use it for diagnosis only.

How many runs prove a fix or a negative result? If the failure rate is p, the probability that N consecutive runs all pass by luck is (1 - p) to the power N. For 95 percent confidence that a pass is not luck, you need roughly 3 divided by p runs. At p = 0.10 that is about 29 runs; at p = 0.01 about 300 runs. Report the number you actually ran. A single green run after an intermittent failure proves nothing.

### Reproducing CI-only and UI failures

For a failure seen only in CI, read the CI log before trying to recreate it. The GitHub CLI can show it read-only: `gh run view <run-id> --log-failed` prints the logs of failed steps, `gh run view <run-id> --job <job-id> --log` prints one job's full log, and `--attempt <n>` selects a retry. These commands read only. Then compare the CI runner's environment (versions, environment variables, parallelism, resource limits) with yours. Do not re-run, cancel or edit workflows: re-running a run writes to the remote and needs user approval.

For a UI failure, reproduce with browser automation against a local or test deployment only. Record the browser, viewport and steps. When using Playwright, a trace records actions, DOM snapshots, console output and network requests with headers and bodies; run `npx playwright test --trace on` to record locally and `npx playwright show-trace <trace.zip>` to open it. Traces can contain tokens and personal data in headers and bodies, so treat a trace as sensitive, keep it in scratch space and delete it afterwards.

### The attempt log and when to stop

Keep a log; each attempt must differ from the last in at least one named variable. After 3 documented attempts that varied input, configuration or timing without reproducing, stop and escalate. Do not keep trying the same thing.

Log format:

| # | What I varied | Exact steps | Result | What it rules out |
|---|---|---|---|---|

A useful escalation says what you tried, what you still need (a log from the failing run, the exact build, a data sample with personal data removed, access you lack) and what you would try next.

### Reproduction safety

- Never reproduce against production, and never against real user data. Use synthetic or anonymised data, a local instance or a test environment.
- Do not run commands that delete, migrate, publish, deploy or write to a remote while reproducing. If a reproduction needs one, stop and ask the user, stating the action, target, risk and rollback.
- Keep reproduction scripts and captured outputs in a scratch directory outside the project tree. Delete them and any processes you started before you report.
- Redact secrets and personal data when you copy commands, headers and logs into notes.

## Examples

### Bad to good: the reproduction record

Bad:

```text
Login sometimes fails. Tried it a few times, works on my machine. Probably flaky.
```

Good:

```text
Expected: POST /login with valid credentials returns 200 and a session cookie.
Actual:   returns 500 in 7 of 50 runs; 43 of 50 return 200.
Error:    TypeError: Cannot read properties of undefined (reading 'user')
            at SessionStore.load (src/session.js:58:21)
Revision: a3f9c01, clean tree.
Env:      Node 20.11.1, Linux x86_64, 4 CPUs, TZ=UTC, lockfile revision same as CI.
Command:  for i in $(seq 1 50); do curl -s -o /dev/null -w "%{http_code}\n" \
            -X POST http://localhost:3000/login -d @fixtures/login.json; done | sort | uniq -c
Result:   43 x 200, 7 x 500.
Variation: 1 CPU -> 21 of 50 fail (rate rises under contention).
```

The good version supports the next step: a rate that changes with CPU count points to a race, so isolation starts there.

### Reduction trace

```text
Baseline: 4,000-line import file, fails with "invalid date" at row 2,317.
Cut to rows 2,000-2,500  -> fails   (keep)
Cut to rows 2,250-2,375  -> fails   (keep)
Cut to rows 2,300-2,325  -> fails   (keep)
Cut to row 2,317 only    -> passes  (restore; needs earlier context)
Cut to rows 2,316-2,317  -> fails   (keep)
Row 2,316 sets locale to "de-DE"; row 2,317 is "03/04/2026". Minimal input: 2 rows.
```

### Attempt log

```text
#1 Reported steps, Node 20.11, Linux                    -> not reproduced (50 runs)
#2 Same steps, TZ=America/New_York and a 1-CPU limit    -> not reproduced (50 runs)
#3 Production-shaped synthetic data (10k rows, no PII)  -> reproduced 3 of 20 (row count matters)
```

Attempt 3 changed the data volume, which was the missing variable. Had it failed too, the escalation would list the three rows above and ask for a sample of the real data shape.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Paraphrasing the error message | Searches and comparisons against other reports fail; details such as a path or code are lost | Copy the exact text, redacting only secrets |
| Reducing before reproducing once with the original steps | You may reduce away the actual trigger and never notice | Reproduce unchanged first, save the baseline, then reduce |
| Treating one passing run as "fixed" for an intermittent bug | The failure rate may be low; the pass proves nothing | Measure the rate, then run about 3/p times and report the count |
| Changing several variables per attempt | You cannot tell which change mattered | One variable per attempt, logged |
| Reproducing on production or with real data | Risk of damage and of exposing personal data | Local or test environment with synthetic or anonymised data |
| Recording the manifest range instead of the installed version | The range resolved differently when the bug appeared | Read the lockfile and the installed package version |
| Declaring "cannot reproduce" after one try | Wastes the report and hides an environment dependency | Three varied, logged attempts, then escalate with what is missing |
| Leaving scratch scripts, traces and processes behind | Traces and logs may hold tokens; stray processes skew later runs | Delete scratch files and stop processes, then list them in the report |

## Checklist

- [ ] Expected behaviour, every symptom and the verbatim error are written down.
- [ ] The source revision and whether the tree was clean are recorded.
- [ ] Operating system, runtime, locked dependency versions and relevant configuration are recorded, with secrets redacted.
- [ ] The original steps were run once unchanged before any simplification.
- [ ] A minimal reproduction exists and was run 3 times from a clean start with the same failure.
- [ ] The minimal reproduction shows the same error and failing frame as the original.
- [ ] For an intermittent failure, the failure rate is stated with the run count.
- [ ] No attempt used production systems or real user data.
- [ ] Every attempt in the log differs from the previous in a named variable.
- [ ] Scratch files, traces and processes created for reproduction are deleted.

## Verify with context7 and gh_grep

- **context7:** Resolve the project's test runner, runtime and framework at their locked versions and check: Jest `--runInBand`, `--detectOpenHandles`, `--randomize` and `--seed` behaviour for the installed Jest version; pytest `faulthandler_timeout` and `-x`/`--maxfail` for the installed pytest; the runtime's flags for dumping state on a hang; known issues for the dependency version that match the symptom ("`<library>` `<version>` flaky", "`<library>` `<version>` race condition").
- **gh_grep:** Search the verbatim error text with paths and ids removed, for example `Cannot read properties of undefined (reading` plus the property name; search `faulthandler_timeout` and `--randomize --seed` in CI configuration to see how maintained repositories capture seeds and hang dumps; search `dump_traceback_later(` for real hang-diagnosis usage.

## Sources

- Git documentation, git-bisect and git-worktree manuals (Git 2.56.0 pages): https://git-scm.com/docs/git-bisect.html and https://git-scm.com/docs/git-worktree.html
- Jest CLI options (Jest 30.5): https://jestjs.io/docs/cli
- pytest, How to handle test failures (8.4): https://docs.pytest.org/en/8.4.x/how-to/failures.html
- Python, faulthandler (3.13): https://docs.python.org/3.13/library/faulthandler.html
- Python, Development Mode (3.13): https://docs.python.org/3.13/library/devmode.html
- Playwright, Trace viewer: https://playwright.dev/docs/trace-viewer
- GitHub CLI manual, gh run view: https://cli.github.com/manual/gh_run_view
