# Dependency Security

How to audit dependencies for known vulnerabilities and supply chain risk: tools, advisories, reachability, pinning and provenance; assumes OWASP Top 10:2025 A03 and A08, OSV-Scanner v2 command syntax and SLSA v1.2, checked 2026-11-26. Dependency upkeep and lockfile hygiene are owned by `languages-clean-code`; this file covers assessing risk.

## Contents

- Inventory first
- Auditing tools and approvals
- Triage: advisories and reachability
- Supply chain checks for new and changed dependencies
- Pinning and lockfiles
- Provenance and build integrity
- Rating and reporting

## Guidance

### Inventory first

1. Find every manifest and lockfile in scope (package manifests, lockfiles, requirements files, build files, container base images, CI action references, vendored code, git submodules).
2. Separate direct from transitive dependencies, and runtime from development and build-only ones.
3. For a change, diff the manifests and lockfile against the base revision: `git diff <base>...HEAD -- <manifest and lockfile paths>`. Every added or changed package is in scope, including transitive ones that appear in the lockfile diff.
4. Compare against an SBOM if the project keeps one (SPDX or CycloneDX); OSV-Scanner can read SBOM files.

Adding or majorly upgrading a dependency needs user approval under `AGENTS.md`. Report an unapproved addition as a process finding.

### Auditing tools and approvals

Tools that install packages, call the network or write files need user approval before they run; state the command, the target and what it contacts. Prefer read-only, offline modes when approval is not given.

| Need | Command (confirm with context7 for the installed version) | Note |
|---|---|---|
| Scan a source tree against the OSV database | `osv-scanner scan source -r <dir>` | `scan source` is the default subcommand; contacts the OSV API |
| Scan specific lockfiles | `osv-scanner scan source --lockfile=<path>` | Repeat the flag for several lockfiles |
| Scan offline | `osv-scanner --offline --download-offline-databases <dir>` | Downloads the database once; later scans need no network |
| Scan a container image | `osv-scanner scan image <name:tag>` | Image must be available locally or pullable |
| Scan an SBOM | `osv-scanner --sbom=<file>` | Supports SPDX and CycloneDX file names |
| Ecosystem tools | `npm audit` for npm, `pip-audit` for Python (unverified here) | Use the project's own tool when it exists; check flags with context7 |

Note: `osv-scanner fix` and any `audit fix` style command modify files and lockfiles; they are never run by an auditor.

A scanner reports known issues only. It cannot see malicious packages that are not yet in a database, compromised maintainers, or install-time behaviour. Do not report a clean scan as "dependencies are safe".

### Triage: advisories and reachability

A severity score from an advisory describes the library in general, not this project. Convert it into project risk with these questions, in order.

1. **Is the package really present at runtime?** Development-only and test-only packages that never ship are usually `low` or out of scope; say so.
2. **Is the vulnerable component used?** Find the affected function, module or feature named in the advisory and search the code for calls. If your project never calls it, mark not reachable (and note that a transitive call inside another library may still reach it).
3. **Can attacker-controlled input reach it?** Trace from entry points. Input only from trusted internal sources lowers likelihood.
4. **Are preconditions met?** Some advisories need a specific configuration, platform or option.
5. **Is a fix available, and is it safe to take?** Name the fixed version. A major upgrade needs approval and tests.
6. **Is there a mitigation if no fix exists?** Disable the feature, add input limits, isolate the component, or replace the dependency (see supply chain below).

Some scanners offer call analysis for specific languages (OSV-Scanner has an experimental `--call-analysis` option); treat its output as a hint to verify by reading the code, not as proof.

Outcomes: reachable and exploitable with attacker-controlled input is `high` or `critical`; present but unreachable is `low` with a note; reachability unknown is reported with confidence `needs verification`, never rounded up to `high`. When no alternative exists and a vulnerability or suspicious provenance remains, escalate as a supply chain risk without a mitigation path.

### Supply chain checks for new and changed dependencies

A03:2025 widens the old "vulnerable and outdated components" to compromise anywhere in dependencies, build systems and distribution. For each new or substantially changed dependency check:

- **Need:** does the project need it, or is a few lines of code or an existing library enough? Fewer dependencies is fewer risks.
- **Identity:** the package name matches the intended project (look for near-identical names of popular packages), the source repository link is consistent, and the publisher is the expected one. Names that match an internal package name in a public registry are a dependency confusion risk; check registry scoping configuration.
- **Health:** recent maintenance, a security policy, a reasonable maintainer base, and a history of fixing issues. These are signals, not guarantees.
- **Behaviour at install:** install-time scripts (lifecycle hooks), native build steps, network calls at install, and post-install downloads. Read them for new packages.
- **Transitive weight:** how many new transitive packages arrive with it.
- **Licence:** compatibility is a legal and product decision; flag unknown or restrictive licences to the user.
- **Source of the artifact:** installed from the intended registry, over TLS, with integrity values recorded in the lockfile.

### Pinning and lockfiles

- A lockfile exists, is committed, and the build installs strictly from it. Check the install command in CI and the Dockerfile uses the lockfile-respecting form for the ecosystem (for example `npm ci` rather than `npm install`; for Python, a requirements file with hashes and the hash-checking install option; confirm with context7 for the tool version).
- Version ranges in manifests are acceptable only with a lockfile that fixes the resolved version and integrity hashes.
- Container base images: pin by digest for production builds and record the tag in a comment. Floating tags change under you.
- CI actions and reusable workflows: pin third-party actions to a full-length commit SHA, not a tag. Tags can be moved if a maintainer account or repository is compromised; a SHA is immutable. Verify the SHA belongs to the action's own repository and not a fork. GitHub offers policies at repository and organisation level that require SHA pinning.
- Build tools and scripts fetched during the build (`curl | sh` patterns, downloaded binaries) are fixed to a version and verified by checksum or signature.
- Automated update tooling should open reviewable pull requests; unattended auto-merge of dependency updates is a risk to report for high-risk repositories.

### Provenance and build integrity

SLSA (Supply-chain Levels for Software Artifacts) v1.2 is the current specification version; its stable Build track has three levels.

| Level | Meaning | Protects against |
|---|---|---|
| Build L1 | Provenance exists describing how the artifact was built | Mistakes; helps debugging and inventory |
| Build L2 | Signed provenance generated by a hosted build platform | Tampering after the build |
| Build L3 | Hardened build platform | Tampering during the build |

Audit questions for the project's own artifacts: are release artifacts built by CI rather than from developer machines, does the build produce provenance, can a consumer verify it, and does the pipeline's write access follow least privilege (see [infrastructure-security.md](infrastructure-security.md))? For consumed packages: does the ecosystem publish provenance or signatures, and does the project verify them? Package-registry signature and provenance verification commands differ by ecosystem and version; confirm with context7 before recommending one (unverified here).

Integrity failures beyond dependencies (A08:2025): unsigned auto-updates, untrusted deserialisation of downloaded data, and artifacts promoted to production without checking they came from the expected build.

### Rating and reporting

| Situation | Rating guidance |
|---|---|
| Known-exploited or trivially exploitable issue, reachable, attacker input, production | `critical` |
| Reachable with plausible preconditions; serious impact | `high` |
| Present at runtime, limited reachability or impact | `medium` |
| Development-only, not reachable, or hardening advice | `low` |
| Reachability unknown | Report with `needs verification`; list the check needed |
| Suspicious package, name similarity or unexplained install script | At least `high` until explained; escalate |

Each dependency finding states: package and resolved version, advisory identifier, affected component, reachability reasoning with file and line, fixed version, whether the fix is a major change, and a verification step (re-run the scan, run the relevant tests). Separate introduced dependencies from pre-existing ones.

## Examples

### Triage record (filled in)

```
Package: <PACKAGE> 4.2.1 (transitive via <PARENT> 2.0.3), runtime
Advisory: <ADVISORY-ID>, affects the <FEATURE> parser, fixed in 4.2.4
Reachability: <PARENT> calls the parser in src/import/csv.ts:40 with user-uploaded files -> attacker-controlled input reaches it.
Preconditions: default configuration; no mitigation present.
Fix: 4.2.4 is a patch release; needs user approval to change the lockfile.
Rating: high (introduced by this change, reachable)
Verify: re-run the dependency scan; run the import tests with an oversized and malformed file.
```

### Unreachable advisory

```
[low] <PACKAGE> 1.9.0 has advisory <ADVISORY-ID> in <FEATURE>
Location: package.json:22
Category: OWASP A03:2025
Evidence: no call to <FEATURE> found in project code; package used only by a build script (devDependencies).
Impact: none at runtime in current use.
Likelihood: not reachable.
Remediation: upgrade at the next routine update; no action on this change.
Confidence: probable (transitive calls inside other libraries were not traced)
```

### CI action pinning: bad to good

```yaml
# Bad: a tag can be moved to different code
- uses: actions/checkout@v4

# Good: immutable full-length commit SHA with the version in a comment
- uses: actions/checkout@<FULL_COMMIT_SHA> # v4.x.y
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reporting every scanner hit at the advisory's severity | Noise hides the real risks | Assess reachability and rate by project risk |
| Ignoring transitive dependencies | Most hits arrive indirectly | Read the lockfile and trace which direct package pulls them |
| Declaring "no vulnerable dependencies" after a clean scan | Scanners miss new or malicious packages | State the tool, date, database and what it cannot see |
| Running fix commands during an audit | Changes files and versions without approval | Report and recommend; the implementer acts after approval |
| Floating tags for images and actions | Content changes without review | Pin by digest or full SHA with a version comment |
| Approving a package on popularity alone | Name similarity and compromised maintainers exist | Check identity, install scripts and publisher |
| Treating a lockfile as optional | Builds differ between machines and over time | Commit it and install strictly from it |

## Checklist

- [ ] All manifests, lockfiles, image bases and CI references in scope were inventoried.
- [ ] Added and changed packages in the diff, including transitive ones, were reviewed.
- [ ] Scanning commands that use the network or write files had user approval, or the gap is stated.
- [ ] Each advisory has reachability reasoning with file and line, or `needs verification`.
- [ ] New dependencies were checked for need, identity, install scripts and publisher.
- [ ] A committed lockfile exists and the build installs from it.
- [ ] Container images and third-party CI actions are pinned to immutable references.
- [ ] Downloaded build tools are verified by checksum or signature.
- [ ] Release artifacts are built by CI, and provenance status is recorded.
- [ ] Introduced and pre-existing dependency issues are reported separately.
- [ ] Dependency additions or major upgrades had user approval.

## Verify with context7 and gh_grep

- **context7:** query the project's package manager docs for "audit command and flags", "install strictly from lockfile", "ignore install scripts", "verify signatures or provenance"; query OSV-Scanner documentation for "scan source", "scan image", "offline mode" and "call analysis"; query the CI platform for "pin actions to a commit SHA policy".
- **gh_grep:** search literal code: `npm ci`, `--ignore-scripts`, `--require-hashes`, `@sha256:`, `uses: ` with a 40-character reference, `osv-scanner scan`, `provenance`. See how maintained repositories pin and verify.

## Sources

- OWASP Top 10:2025 Introduction (A03 Software Supply Chain Failures scope; A08 Software or Data Integrity Failures): https://top10.owasp.org/2025/0x00_2025-Introduction/
- OSV-Scanner usage, source scanning: https://google.github.io/osv-scanner/usage/scan-source
- OSV-Scanner repository README (image scanning, offline mode, supported ecosystems): https://github.com/google/osv-scanner
- OSV-Scanner usage page (SBOM, call analysis): https://google.github.io/osv-scanner/usage/
- SLSA specification, security levels (v1.2 current; Build L1 to L3): https://slsa.dev/spec/v1.0/levels
- GitHub Docs, Secure use reference (pin actions to full-length commit SHA, SHA pinning policy): https://docs.github.com/en/actions/reference/security/secure-use
