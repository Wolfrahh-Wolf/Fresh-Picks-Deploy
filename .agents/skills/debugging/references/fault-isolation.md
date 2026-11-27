# Fault Isolation

How to narrow a reproduced failure to its cause with falsifiable hypotheses, bisection (inputs, configuration, dependencies and commits), `git bisect` and differential testing; assumes Git 2.x (manual checked at 2.56.0) and the project's own test tooling, checked 2026-11-26.

## Contents

- Hypotheses that can be wrong
- One variable at a time
- Bisecting inputs, configuration and dependencies
- Finding the change: `git log` search and `git bisect`
- Running `git bisect` safely
- Writing the bisect script
- Differential testing
- Recording the elimination matrix

## Guidance

### Hypotheses that can be wrong

Collect evidence first (see [logging-tracing.md](logging-tracing.md)), then write hypotheses. A hypothesis is useful only if an observation could disprove it.

Format every hypothesis the same way:

```text
H<n>: <statement about the cause, naming a component and a mechanism>
Predicts: <what you would observe if true>
Disproved by: <the observation that would prove it false>
Cheapest test: <one action>
Status: open | confirmed | disproven | untestable
```

Rules:

- Cap the live list at 5. If a sixth appears, rank and drop the weakest, recording it as `untestable` with the reason, or finish testing one first.
- Reject statements that cannot fail: "something is wrong with the cache" is not a hypothesis; "the cache returns an entry written before the schema change because the key lacks a version" is.
- Rank by how well each explains **all** symptoms, then by test cost. Test a cheap, plausible hypothesis before an expensive, slightly likelier one.
- Include one hypothesis that blames your own assumptions (wrong environment, stale build, wrong file executed, test data differs). A surprising number of failures are a stale artefact.
- When a test result contradicts a hypothesis, record the observation and mark it disproven. Do not adjust the hypothesis until it survives; write a new one.
- If all hypotheses are disproven, list the assumptions you made while writing them, check each assumption directly, and rewrite. If none remain after that, escalate with the full elimination matrix.
- The first explanation that comes to mind is often wrong. Do not skip evidence collection because one feels obvious.

### One variable at a time

Change exactly one thing per experiment, so the result can only be attributed to that thing. Before each experiment write down which hypotheses it will separate. After it, record:

```text
Changed: <the one variable>   Observed: <result, verbatim>   Eliminates: <H ids>   Supports: <H ids>
```

When two variables look coupled, vary one, restore it, then vary the other. If the failure appears only when both change, that interaction is the finding.

Prefer experiments that **split the remaining possibilities in half** over experiments that test a single guess. A test that rules out half the code path is worth more than one that rules out a single line.

Do not edit project source to run an experiment. Make the change in a disposable copy outside the project tree, or use configuration, environment variables and command-line options that need no edit. Delete the copy afterwards.

### Bisecting inputs, configuration and dependencies

Binary search applies to any ordered or divisible set. Each step halves the suspects, so 1,000 candidates need about 10 tests and 1,000,000 need about 20.

| Search space | How to halve it | Stop when |
|---|---|---|
| Input data (rows, records, lines) | Run the first half, then the second | One record, or the smallest set that fails |
| Request or payload fields | Remove half the optional fields | The failing field or pair of fields |
| Configuration options | Reset half to defaults | The option whose value matters |
| Feature flags | Disable half | The flag or the flag pair |
| Middleware or pipeline stages | Skip half, or call the second half directly with captured input | The stage that produces the bad value |
| Test order (order-dependent failures) | Run half of the preceding tests, then the failing test | The single test that pollutes shared state |
| Dependency versions | Pin the middle version between the last good and first bad | Adjacent good and bad releases |
| Data across a pipeline | Inspect the value at the midpoint stage: is it already wrong? | The first stage whose output is wrong |

The last row is the cheapest isolation tool for data flow: find the **first place the data is wrong**, not the place the error is raised. An exception is reported where the bad value is used; the cause is where it was produced.

Pitfalls: if the failure is intermittent, repeat each step enough times to trust a "pass" (about 3 divided by the failure rate; see [bug-reproduction.md](bug-reproduction.md)). A "pass" that depends on luck sends the search to the wrong half. If a step cannot be tested (the build breaks), skip it and note it; do not mark it good.

For a dependency suspected of a regression, compare the lockfile at the last good and the first bad revision first: `git diff <good>..<bad> -- <lockfile>` lists exactly what moved. Then check the library's changelog and known issues for the versions involved with **context7**, and treat what you find as a hypothesis to reproduce.

### Finding the change: `git log` search and `git bisect`

If you know a symbol, string or function is involved, search history before bisecting; it is often faster.

| Question | Command |
|---|---|
| Which commits added or removed this string (changed its occurrence count)? | `git log -S "<string>" --oneline` |
| Which commits changed a line matching this pattern? | `git log -G "<regex>" --oneline` |
| How did this function change over time? | `git log -L :<function>:<path>` |
| What changed between the last good and first bad revision? | `git log --oneline <good>..<bad>` and `git diff <good>..<bad> -- <path>` |
| Who last touched these lines, and in which commit? | `git blame -L <start>,<end> <path>` |

`-S` finds commits that change how many times a string occurs, so a commit that only edits surrounding lines does not match; `-G` matches commits whose diff contains a changed line matching a regular expression. Both read only. A commit found this way is a suspect, not a conclusion: you must still prove it is the cause (see [root-cause-analysis.md](root-cause-analysis.md)).

Use `git bisect` when the failure is a **regression** (it worked before, with a known good revision) and the failing check can be run mechanically on any commit. It does a binary search over history, so a range of 1,000 commits needs about 10 test runs.

Command forms:

| Command | Effect |
|---|---|
| `git bisect start [<bad> [<good>...]]` | Begin; optionally name the bad and good revisions |
| `git bisect bad [<rev>]` and `git bisect good [<rev>...]` | Mark the current or a named revision |
| `git bisect new` and `git bisect old` | Same as bad and good; clearer when hunting for a change that is not a bug |
| `git bisect start --term-old <word> --term-new <word>` | Use your own terms, for example `slow` and `fast` |
| `git bisect run <cmd> [<args>]` | Automate: run the command at each step |
| `git bisect skip [<rev-or-range>]` | The revision cannot be tested |
| `git bisect log` | Print what has been marked so far |
| `git bisect replay <logfile>` | Re-apply a saved log, for example to correct a wrong mark |
| `git bisect visualize` | Show the remaining suspects |
| `git bisect reset [<commit>]` | End the session and return to the starting commit |

Useful options on `start`: `--first-parent` follows only the first parent at merges, so a merge commit is reported as the introduction of the bug and the ancestor commits of a merged branch are ignored; use it when a merged branch contained broken or unbuildable commits but the merge itself was fine. `--no-checkout` updates the reference `BISECT_HEAD` instead of checking out each commit; use it when the check does not need a working tree. Custom terms cannot be mixed with `good` and `bad` in one session, and cannot reuse subcommand names such as `reset` or `start`.

### Running `git bisect` safely

`git bisect` checks out old commits and rewrites the working tree at every step. In the user's working tree that destroys uncommitted work and disturbs files other agents may be using, and the debugger edits nothing in the project. Always bisect in a disposable linked worktree outside the project tree.

```bash
# 1. Create a throwaway worktree with a detached HEAD, outside the repository directory.
git worktree add --detach <scratch-dir>/bisect-work <bad-revision>
cd <scratch-dir>/bisect-work

# 2. Bisect there.
git bisect start <bad-revision> <good-revision>
git bisect run <script-or-command>
git bisect log > <scratch-dir>/bisect.log     # keep the evidence

# 3. Clean up, always, including after errors.
git bisect reset
cd <project-root>
git worktree remove --force <scratch-dir>/bisect-work
```

Notes:

- Bisect state is per worktree (the references under `refs/bisect` are not shared), so this does not disturb the main worktree.
- `git worktree remove` refuses to delete a worktree with modified or untracked files unless forced; `--force` here only deletes your own scratch checkout. Confirm the path is your scratch directory before you run it.
- Dependencies and build outputs are not versioned. Install and build inside the worktree at every step (the script does this), and never point a step at the main worktree's `node_modules` or virtual environment.
- Creating a worktree is local. Do not push, tag, fetch with pruning or alter any remote. Those need user approval under `AGENTS.md`.
- If you cannot make a worktree (a very large repository, no disk space), report that and fall back to bisecting inputs and configuration, or ask the coordinator for a decision.

### Writing the bisect script

The script decides good, bad or untestable from its exit status. For `git bisect run`:

| Exit status | Meaning |
|---|---|
| 0 | The revision is good (old) |
| 1 to 127 except 125 | The revision is bad (new) |
| 125 | The revision cannot be tested; skip it |
| Any other (128 and above) | Abort the bisect |

A status above 255 is truncated, so `exit -1` becomes 255 and aborts the run. Exit 125 for anything that is not the failure you are hunting: a build break, a missing dependency, a failed install. If you let a build failure return a bad status, bisect will blame the wrong commit.

```bash
#!/bin/sh
# check.sh -- run at each bisect step from the repository root of the scratch worktree.
set -u
npm ci --silent         || exit 125   # cannot install -> untestable
npm run build --silent  || exit 125   # cannot build   -> untestable
# The failure under investigation: exit 0 if the test passes, 1 if it fails.
npx jest -t "<failing test name>" --silent
```

Rules for the script:

- Test **exactly the failure you reproduced**, using the same command and the same test. A different failure at an old commit misleads the search.
- Make it deterministic. For an intermittent failure, loop inside the script and return bad if any of N runs fails, with N from the run-count rule above. A good verdict needs the full N passes.
- Keep it fast and self-contained; it runs about log2 of the range times.
- Keep it outside the repository (in the scratch directory), because checking out old commits will not carry an untracked file and a tracked one will be replaced.

If more than one commit cannot be tested, the answer may be a range rather than a single commit, because skipping a commit adjacent to the culprit leaves git unable to say which of them is first bad. Report the range and say why.

Read the result: git prints "`<hash>` is the first bad commit" with the commit message. Then verify it independently: check out its parent and it itself, run the reproduction on each, and read its diff. The commit that introduced the change is a **trigger or a cause candidate**; whether it is the root cause is decided in [root-cause-analysis.md](root-cause-analysis.md).

### Differential testing

Differential testing compares two runs that should behave the same and finds where they diverge. It works when you have a working and a failing variant of anything.

| Axis | Working side | Failing side | What you compare |
|---|---|---|---|
| Environment | A machine or container where it passes | One where it fails | The environment table in `bug-reproduction.md`, line by line |
| Version | Last good release | First bad release | Lockfile, built output, behaviour on the same input |
| Input | A passing input | A failing input | The smallest difference that flips the result |
| Path | The branch that works | The branch that fails | The first divergent intermediate value |
| Implementation | A reference implementation, an older version or a second library | The code under test | Outputs for the same inputs |
| Mode | Serial, debug or single-thread | Parallel, optimised or multi-thread | Whether the failure depends on concurrency or optimisation |

Procedure:

1. Make both sides produce the same observable artefact: a log, a response body, a dumped data structure, a list of installed packages.
2. Normalise noise before comparing: timestamps, random ids, absolute paths, ordering of unordered collections. A diff full of noise hides the signal.
3. Diff, and read the **first** difference in execution order, not the largest.
4. Treat each difference as a hypothesis. Apply it to the failing side alone and re-run (one variable at a time). Keep only differences that change the outcome.

For a version hunt, the same idea gives you a search: with versions v1 (good) through vN (bad), test the middle one and halve, exactly as in `git bisect`.

### Recording the elimination matrix

Keep one table for the whole investigation. It is the evidence you hand over if you escalate, and the proof you give if you conclude.

| Hypothesis | Test | Observation | Disposition |
|---|---|---|---|
| H1 | <what you did> | <verbatim result> | confirmed, disproven or untestable |

An `untestable` entry names why (needs production access, no instrumentation available, cannot be isolated) and what would make it testable. A hypothesis that is neither confirmed nor disproven does not count as eliminated.

## Examples

### Hypothesis list with dispositions

```text
Symptom: GET /reports/42 returns totals that are 1 cent off in about 2% of reports.

H1: Float rounding in the totals function.
    Predicts: wrong values only where sums have more than 2 decimals.
    Disproved by: a wrong total whose line items are all whole cents.
    Result: Report 42 items are 10.10, 20.20, 30.30 -> wrong total. Consistent. Status: open.
H2: The database returns stale rows (read replica lag).
    Predicts: totals correct on a re-run a few seconds later.
    Disproved by: the same wrong total after 60 s, and from the primary.
    Result: same wrong total from the primary after 60 s. Status: disproven.
H3: The report cache serves an old total.
    Predicts: cache entry timestamp earlier than the last item edit.
    Result: entry written after the last edit. Status: disproven.
H4 (assumption check): The test fixture differs from the real data.
    Predicts: different currency or precision column type.
    Result: fixture uses integer cents; production column is numeric(12,4). Status: confirmed as a difference, so tests did not cover this path.
```

H1 remains: test it directly by summing the three captured values with the function's own arithmetic in a scratch script and compare with the integer-cent result.

### `git bisect run` end to end

```bash
git worktree add --detach /tmp/dbg-work/bisect-work a3f9c01
cd /tmp/dbg-work/bisect-work
git bisect start a3f9c01 v4.2.0         # bad first, then good
git bisect run /tmp/dbg-work/check.sh
```

Typical end of output, abbreviated:

```text
running '/tmp/dbg-work/check.sh'
...
7b21e4d is the first bad commit
commit 7b21e4d...
    Replace money helper with plain arithmetic
bisect found first bad commit
```

Then:

```bash
git bisect log > /tmp/dbg-work/bisect.log
git bisect reset
cd <project-root> && git worktree remove --force /tmp/dbg-work/bisect-work
```

The report records the log, the commit, and the next step: verify that reverting the logic of `7b21e4d` in a scratch copy removes the failure.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Running `git bisect` in the user's working tree | Checks out old commits over uncommitted work and changes files other agents use | Use a disposable detached worktree outside the project and remove it afterwards |
| Letting a build failure return exit status 1 in the script | Bisect blames the first commit that failed to build | Return 125 for anything that is not the failure under investigation |
| Bisecting on a different failure than the reproduced one | The search converges on an unrelated change | Run the exact reproduced test or command at every step |
| Trusting one pass on an intermittent failure | Wrong half is discarded; the result is noise | Loop N runs per step and treat any failure as bad |
| Changing two variables in one experiment | The outcome cannot be attributed | One variable per test, logged |
| Keeping a hypothesis alive by reinterpreting it | You stop learning; confirmation bias | Mark it disproven and write a new one |
| Reading the first bad commit as the root cause | The commit may only have exposed an older latent defect | Prove the cause with a counterfactual; classify trigger versus cause |
| Diffing without normalising timestamps, ids and ordering | The real difference is buried | Normalise, then read the first difference in execution order |
| Skipping many commits in a row | The result becomes a range; the culprit may be one of the skipped | Make the commits testable (build fix in the script) or report the range |
| Investigating where the error is raised, not where the data first went wrong | The symptom site is rarely the cause | Find the first stage whose output is already wrong |

## Checklist

- [ ] Each hypothesis states a mechanism, a prediction and a disproving observation.
- [ ] No more than 5 hypotheses are open at once.
- [ ] One hypothesis tests an assumption about the environment or build.
- [ ] Every experiment changed exactly one variable and its result is recorded.
- [ ] Experiments ran on a disposable copy or through options that need no source edit.
- [ ] `git bisect` ran in a detached worktree outside the project tree.
- [ ] The bisect script uses exit status 125 for revisions it cannot build or test.
- [ ] The bisect script runs the exact reproduced failure, repeated enough for an intermittent one.
- [ ] The first bad commit was checked by running the reproduction on it and on its parent.
- [ ] `git bisect reset` was run and the worktree was removed; `git worktree list` shows only the project.
- [ ] The elimination matrix lists every hypothesis with a disposition and evidence.

## Verify with context7 and gh_grep

- **context7:** Check the version-specific behaviour of the tools you drive: the test runner's single-test selection and ordering flags at the locked version; the package manager's clean-install command (for example the exact behaviour of `npm ci`); known issues and changelog entries for the dependency range between the last good and first bad lockfile; whether a runtime flag you plan to vary exists in the installed version.
- **gh_grep:** Search `git bisect run` and `exit 125` in CI and tooling repositories to see real bisect scripts; search `git log -S` and `git worktree add --detach` for real usage; search the verbatim error for reports that name the same dependency version.

## Sources

- git-bisect manual (last updated in Git 2.56.0): https://git-scm.com/docs/git-bisect.html
- git-worktree manual (Git 2.56.0): https://git-scm.com/docs/git-worktree.html
- Pro Git, Git Tools, Searching: https://git-scm.com/book/en/v2/Git-Tools-Searching
- Jest CLI options (Jest 30.5): https://jestjs.io/docs/cli
