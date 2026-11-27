# Technology Evaluation

How to compare technologies and write a recommendation: criteria, weights, maturity, maintenance, licence, exit cost. Assumes SPDX licence identifiers, OpenSSF Scorecard check names and Semantic Versioning 2.0.0 as read on 2026-11-26; the project's own manifest and recorded decisions win over anything here.

## Contents

- When an evaluation is worth doing
- Frame the decision and the option set
- Gates versus weighted criteria
- Criteria, weights and scoring
- Maturity signals
- Maintenance signals
- Licence
- Exit cost and lock-in
- Total cost of ownership
- Sensitivity check
- Recommendation format
- Handing the result on

## Guidance

### When an evaluation is worth doing

Evaluate when the choice is costly to reverse: a new runtime dependency, a datastore, a framework, a hosted service, a protocol. Do not evaluate when the project already has a recorded choice for the same job (check `docs/adr/`, `docs/ARCHITECTURE.md` and the existing code); reuse it unless there is a stated reason not to. Do not evaluate trivial, easily reversible choices (a small formatting helper used in one file); pick the option that already exists in the project and say so.

A new dependency needs a recorded reason, so the evaluation output feeds an ADR. For ADR rules and numbering, load `system-architecture`.

### Frame the decision and the option set

Write down, in this order, before looking at any candidate:

1. **Job to be done:** one sentence, in terms of behaviour, not product ("retry failed outbound calls with backoff", not "pick a resilience library").
2. **Hard constraints:** runtime and language versions, platforms, licence policy, hosting, data residency, offline use, budget, team skills. These become gates.
3. **Quality targets:** measurable where possible (p95 latency, memory ceiling, throughput, bundle size). If a target is not measurable, mark it **open** rather than inventing a number.
4. **Option set:** at least two real candidates plus the baseline. The baseline is always one of: keep the current approach, use the platform's built-in feature, or write a small amount of own code. Include it even if it looks unattractive; it is the honest comparison for the cost of adding a dependency.

Keep the set small (three to five). Screen out candidates quickly with the gates below instead of scoring everything.

### Gates versus weighted criteria

A gate is pass or fail. Never trade a failed gate against a good score elsewhere.

| Typical gates | Test |
|---|---|
| Runtime and platform support | Supports the project's language, runtime and OS versions, per official docs for those versions |
| Licence acceptable to the project | SPDX identifier read from the licence file is on the project's allowed list, or the user approves |
| Required capability exists | Each must-have requirement is met by documented behaviour, not by plugin promises |
| Not abandoned | Has a release or maintainer response inside the window you set (see maintenance signals) |
| Security must-haves | For vulnerability assessment of a candidate, load `security-engineering` |

Everything that survives the gates is compared with weighted criteria.

### Criteria, weights and scoring

Fix the weights before scoring and write them down. Weights sum to 100. Start from the table and adjust to the decision; explain every change in one line.

| Criterion | Default weight | What earns a high score (4 to 5) |
|---|---|---|
| Fit to requirements | 25 | Meets every must-have and most should-haves with documented, supported behaviour |
| Maturity and stability | 15 | Stable major version, clear compatibility policy, low rate of breaking changes |
| Maintenance health | 15 | Recent releases, responsive maintainers, more than one active maintainer |
| Ecosystem and integration | 10 | Works with the project's existing stack without adapters; good tooling and types |
| Operability and team fit | 10 | Team already knows it, or learning cost is small; good errors and observability |
| Performance and footprint | 10 | Measured on representative data and within targets (see the feasibility reference) |
| Exit cost | 15 | Replacing it later is a bounded, estimated job; data is exportable |

Score each option 0 to 5 per criterion and write the evidence next to the score: a URL, a version, a measurement or a command output. A score without evidence is **unverified** and must say so. Do not average away a zero: a zero on a must-have is a failed gate.

Weighted total = sum of (weight x score) / 5, giving a result out of 100. Treat differences under about 5 points as a tie and decide on the tie-breakers: more reversible, simpler to operate, already in the project.

### Maturity signals

Collect facts, not impressions:

- **Version and compatibility policy:** is there a stable major version (1.0.0 or higher)? Under Semantic Versioning, anything may change at any time while the version is 0.y.z, so a 0.y.z dependency needs a stated reason and a pinned version. Does the project say what its public API is and how it deprecates things?
- **Breaking-change history:** read the changelog for the last two major versions. Count breaking changes per year and check whether each shipped with a migration guide.
- **Support windows:** runtimes and platforms publish release phases (for example Node.js separates Current, Active LTS and Maintenance LTS, and says production applications should use only Active or Maintenance LTS releases). Check the candidate's own support policy and whether it lines up with the project's runtime.
- **Production use:** named adopters in documentation, or several independent maintained repositories using it (find them with gh_grep; see [gh-grep.md](gh-grep.md)).
- **Documentation quality:** reference, guides and an upgrade path for the exact version.
- **Test and CI health:** tests run in CI and pass on the default branch.

Stars, downloads and social buzz measure popularity, not fitness. Record them only as context, never as a scored criterion.

### Maintenance signals

Check these on the day, and write the date:

| Signal | Where to look | Worrying sign |
|---|---|---|
| Last release | Releases or tags page, registry page | None in over 12 months for a fast-moving ecosystem (adjust for stable, finished libraries) |
| Issue and pull request response | Open issues sorted by oldest | Security or crash reports unanswered for months |
| Maintainers | Contributors graph, governance or maintainers file | One active maintainer ("bus factor" of one) with no succession note |
| Status statements | README banner, archived flag, deprecation notice on the registry | Archived, "no longer maintained", or "use X instead" |
| Release automation | Release workflow, signed releases | Manual, undocumented releases |
| Security policy | Security policy file | None, with no way to report a problem |

The OpenSSF Scorecard automates several of these checks (Maintained, Security-Policy, License, Code-Review, Dependency-Update-Tool, Signed-Releases) and scores each 0 to 10. Use it as a quick signal, run it read-only (`scorecard --repo=github.com/<owner>/<repo> --checks=Maintained,Security-Policy,License`), and treat a low score as a prompt to look closer, not as a verdict. It needs a GitHub token in its environment and supports macOS and Linux; ask the user before supplying one. For the vulnerability side of Scorecard, load `security-engineering`.

An archived or officially deprecated project fails the "not abandoned" gate. A stable library with no recent releases because it is finished can still pass; say why you believe it is finished (a statement from the maintainers, no open defects, compatibility with current runtimes verified).

### Licence

1. Read the licence file in the repository at the release you would use, and the licence field of the package on its registry. Record the SPDX identifier (for example `MIT`, `Apache-2.0`, `GPL-3.0-only`). SPDX expressions combine identifiers with `AND`, `OR` and `WITH`; for `A OR B`, the licensee chooses.
2. A repository with no licence grants no rights: default copyright applies, and viewing or forking on a hosting service does not license reuse. Treat "no licence" as a failed gate and tell the user.
3. Check whether the licence conditions fit the project's distribution model: permissive licences ask mainly for attribution; copyleft licences add obligations when you distribute or, for network-copyleft licences, when you offer the software as a service. Report the obligation in one sentence; do not interpret edge cases.
4. Dependencies of the candidate bring their own licences. Note when the candidate's dependency tree contains a licence the project does not allow, and ask for a licence scan by the project's tooling.
5. Source-available and "fair-code" licences are not open-source licences. Flag them separately.

This is not legal advice. When the licence question affects distribution, escalate to the user with the facts.

### Exit cost and lock-in

Exit cost is the cost of replacing the technology after the project depends on it. Estimate it for each option, in person-days with a range, and name what drives it:

- **Surface area:** how many files import it directly? Search the code of a spike or an existing use to count call sites.
- **Data and format lock-in:** can data be exported in an open format? Are stored formats proprietary?
- **Behavioural coupling:** does business logic depend on quirks (ordering, error shapes, retries)?
- **Contractual and operational:** hosted services add account, pricing and API-limit lock-in; self-hosted ones add operational ownership.
- **Standards:** an implementation of an open standard or protocol is cheaper to leave than a proprietary API.

Reduce exit cost only where the saving is larger than the cost of the seam. A thin adapter around a hosted service that the project uses in two places is cheap; an abstraction layer over everything "in case" is speculative and is not recommended. State the seam, if any, as a design suggestion for the architect.

### Total cost of ownership

Add what the criteria do not capture: licence or subscription cost, hosting and egress, usage-based limits (rate limits and quotas that could bind at the target load), training time, and the cost of keeping up with its release cadence. Adding a paid service needs user approval.

### Sensitivity check

Change the weights by plus or minus 5 points on the top three criteria, and drop the least evidenced criterion. If the winner changes, report that the ranking is fragile and name the criterion it depends on. If the winner holds, say so in one line.

### Recommendation format

Lead with the answer. Keep it to one page.

1. **Recommendation:** the option, the version range, and whether it is a new dependency (approval needed).
2. **Why:** two or three reasons tied to the requirements.
3. **Comparison table:** gates, weighted scores with evidence, licence, exit cost.
4. **Rejected options:** each with a concrete reason.
5. **Risks and mitigations:** including what would make the choice wrong.
6. **Unverified and open:** claims you could not confirm, measurable targets still open.
7. **Next step:** approval needed, ADR to write, spike to run.

### Handing the result on

The architect records the decision in `docs/adr/` and updates `docs/ARCHITECTURE.md`. The implementer and debugger report the finding under `Docs impact` and leave the files to their owners. Durable pitfalls (for example, "library X 3.x changed the default timeout") are suggested for `docs/MEMORY.md` through the coordinator.

## Examples

### Bad to good: the recommendation

Bad:

```text
Use Library B. It has 20k stars and everyone uses it.
```

Good (illustrative, figures are placeholders for the shape of the write-up):

```text
Recommendation: adopt Library A 2.x for background jobs (new dependency, approval needed).
Why: only option meeting the "survive process restart" must-have without a new
datastore; same runtime as the app; exit cost is low (jobs are plain functions).
Gates: all three pass. Licence: A = MIT, B = Apache-2.0, C (baseline: cron + script) = own code.
Rejected: B needs a separate broker service (new operational component, +3 to 5 person-days).
Risks: A has two active maintainers; mitigate by pinning and reviewing releases quarterly.
Unverified: A's behaviour under 10k queued jobs (spike proposed, 2 hours).
```

### Filled-in weighted comparison (illustrative numbers)

Weights set before scoring: Fit 25, Maturity 15, Maintenance 15, Ecosystem 10, Operability 10, Performance 10, Exit cost 15.

| Criterion (weight) | Library A | Library B | Baseline: cron and script |
|---|---|---|---|
| Fit (25) | 4: meets all must-haves, docs link | 4: meets all must-haves, extras not needed | 2: no retry or persistence |
| Maturity (15) | 4: 2.x stable, migration guide for 1.x | 4: 5.x stable | 4: nothing new |
| Maintenance (15) | 3: last release 3 months ago, two maintainers | 5: monthly releases, organisation-backed | 3: own code to maintain |
| Ecosystem (10) | 4: typed, same runtime | 3: needs adapter | 4 |
| Operability (10) | 4: no extra service | 2: needs broker | 4 |
| Performance (10) | 3: unverified at target load | 4: published benchmarks (vendor) | 2 |
| Exit cost (15) | 4: about 1 to 2 person-days | 2: about 5 to 8 person-days | 5 |
| **Total / 100** | **75** | **71** | **66 (fails a must-have)** |

A 4-point gap between A and B is a tie by the 5-point rule, so the tie-breakers decide: A is simpler to operate and cheaper to leave. The baseline fails the persistence must-have, so it is removed by a gate regardless of its total.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Choosing by stars, downloads or a trending post | Popularity is not fitness; the pick may fail a hard constraint | Gate on constraints first, score with evidence |
| Scoring before fixing weights | Weights drift to favour the option you already like | Write weights and gates first, then score |
| Leaving out the baseline | The cost of adding a dependency is never weighed | Always include "keep current", "built-in" or "own code" |
| Scoring without evidence | Scores cannot be audited or challenged | Put a URL, version, measurement or command output beside each score |
| Treating a failed gate as a low score | A strong total hides an unusable option | Remove options that fail a gate |
| Ignoring licence until late | Late discovery forces rework | Read the licence file for every candidate in the screening step |
| Reading a vendor benchmark as fact | Vendors choose favourable workloads | Mark it **unverified** and measure on representative data |
| Ignoring exit cost | Lock-in is paid later, with interest | Estimate person-days and name the cost drivers |
| Recommending a 0.y.z dependency without comment | Under Semantic Versioning anything may change at any time | State the risk, pin the version, record the reason |
| Installing candidates into the project to try them | Changes the manifest and lockfile without approval | Try candidates in a scratch location per the feasibility reference |

## Checklist

- [ ] The job to be done, hard constraints and quality targets are written before any candidate is named.
- [ ] The option set has at least two real candidates plus the baseline.
- [ ] Gates are listed and every candidate has a pass or fail per gate.
- [ ] Weights were written before scores and sum to 100.
- [ ] Every score has evidence or is labelled **unverified**.
- [ ] Each candidate's licence is recorded as an SPDX identifier read from its licence file.
- [ ] Each candidate has a maintenance check with the date it was made.
- [ ] Exit cost is estimated in person-days with a range for each candidate.
- [ ] A sensitivity check was run and its result is stated.
- [ ] The recommendation names whether approval is needed (new or majorly upgraded dependency, paid service).
- [ ] Rejected options have concrete reasons.
- [ ] The result names the docs to update and their owners.

## Verify with context7 and gh_grep

- **context7:** for each candidate, resolve the library and query the project's version: `<library> <version> supported runtime versions`, `<library> <version> breaking changes since <previous major>`, `<library> <version> deprecated features`, `<library> licence and support policy`. Confirm that each must-have requirement is documented behaviour.
- **gh_grep:** search for real adoption and for the integration shape you would need: `import <name> from "<package>"` or the language's equivalent, the setup call such as `<Library>.configure(`, and a distinctive option key. Open at least two maintained repositories per candidate and check their licence, last commit and the version they pin. See [gh-grep.md](gh-grep.md).

## Sources

- SPDX, handling licence information and the licence list: https://spdx.dev/learn/handling-license-info/
- GitHub Docs, licensing a repository: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- OpenSSF Scorecard README (checks, scoring, command line): https://raw.githubusercontent.com/ossf/scorecard/main/README.md
- Semantic Versioning 2.0.0: https://semver.org/
- Node.js releases (release phases and production guidance, used as an example of a published support policy): https://nodejs.org/en/about/previous-releases
