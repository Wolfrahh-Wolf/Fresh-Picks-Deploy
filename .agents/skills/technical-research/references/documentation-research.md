# Documentation Research

How to find official documentation that matches the exact version in use, read changelogs and migration guides, and cite the result. Assumes Semantic Versioning 2.0.0, Keep a Changelog 1.1.0 conventions and the four-part Diátaxis documentation model as read on 2026-11-26; the project's manifest and lockfile decide the version.

## Contents

- Start from the version, not the library name
- Find the official home
- Get the version-matched pages
- Choose the right kind of page
- Changelogs, release notes and migration guides
- When documentation is missing or ambiguous
- Check documentation against behaviour
- Citing what you found
- Recording and reporting

## Guidance

### Start from the version, not the library name

"How does library X do Y" has no answer until you know which X. Establish the version first:

1. Read the manifest for the declared range, then the lockfile for the resolved version. The resolved version is the one that runs.
2. If both are unclear, ask the package manager or runtime: `npm ls <package>`, `pip show <package>`, `go list -m <module>`, `cargo tree -p <crate>`, or `<tool> --version`. These are read-only.
3. For platforms and runtimes (language runtime, database, browser, operating system), find the version in the project's configuration, container file, CI configuration or runtime version file.
4. Note the major version. Within Semantic Versioning, a major bump signals an incompatible public API change, a minor bump is backward compatible, and while the version is 0.y.z anything may change at any time. So a 0.y.z dependency needs the exact version, not just the major.
5. If the project uses a range that spans a major boundary, report it and research the resolved version.

If the question is about a version the project does not use (an upgrade, a candidate), say which version you researched.

### Find the official home

An official source is one the maintainers publish and control. Verify, do not assume:

- Follow links **from** the package registry page or the repository README **to** the documentation site, not from a search result to the registry. The registry metadata names the homepage and repository.
- Check that the documentation domain is the one the repository's README or the registry links to. Look-alike sites and abandoned mirrors exist.
- Prefer, in this order: the project's documentation site for your version, the documentation folder in the repository at the release tag, the README at the release tag, the installed package's own files (types, comments, bundled docs).
- Platform vendors (cloud, operating system, database, browser) publish their own documentation; use the vendor's site, not a reseller or tutorial site.
- Specifications and standards come from the standards body, at an explicit edition.

When you cannot establish which site is official, say so and label the claims that depend on it **unverified**.

### Get the version-matched pages

Documentation sites often default to "latest", "stable" or "next". Match the version deliberately:

| Situation | What to do |
|---|---|
| Site has a version selector | Select the project's major and minor; check the page footer or header shows it |
| Site shows only the latest docs | Open the repository at the tag for the resolved version (`v<version>` is common, but check the tags list) and read the docs folder there |
| Docs are generated from source | Read the installed package's type declarations, docstrings or generated API reference for that version |
| Only a README exists | Read the README at the tag, then the source of the function in question |
| Documentation covers a newer version than the project's | Treat statements as a candidate behaviour; confirm in the changelog that it exists in your version |

A context7 query is a fast route to the right page when you pass the version; it does not replace reading the official page for anything decisive (see [context7.md](context7.md)).

### Choose the right kind of page

Documentation serves different needs. Pick the page type for the question, using the four Diátaxis kinds:

- **Reference:** exact facts, parameters, defaults, return values, error codes. Use for "what does this option do".
- **How-to guide:** steps to reach a goal. Use for "how do I configure X".
- **Tutorial:** a guided learning path. Use only to learn the shape of an unfamiliar tool, not to settle a detail.
- **Explanation:** background and design rationale. Use for "why does it behave this way".

Reference decides facts. Guides and tutorials often simplify, may omit defaults, and may be written for another version.

### Changelogs, release notes and migration guides

These answer "what changed" and are the best source for version questions.

- **Find them:** a `CHANGELOG` or `CHANGES` file in the repository, the Releases page, a "What's new" or "Upgrading" section of the documentation, or a dedicated migration or upgrade guide for the major version.
- **Read the right span:** every entry between the project's resolved version and the version in question, not only the headline release. For an upgrade question, read the entries for each intermediate release.
- **Look for the standard headings** used by changelogs that follow Keep a Changelog: Added, Changed, Deprecated, Removed, Fixed, Security. Deprecated entries predict the next major's removals; Removed and Changed entries are the breaking ones.
- **Check for an Unreleased section.** It describes code not yet released; do not attribute it to the released version.
- **Breaking changes under Semantic Versioning** live in major versions; if a minor or patch release changes behaviour that the documentation promised, note it as a possible project defect and cite the issue.
- **Runtime deprecation warnings** (printed by the library or runtime at run time) are authoritative evidence of what the installed version considers deprecated. Capture the exact message.
- **Migration guides** name the replacement for each removed API. Prefer the guide's replacement over inventing your own.
- A project without a changelog: read the commit history or release tags between versions (read-only), and say that the changelog is missing.

### When documentation is missing or ambiguous

Work down this list and stop at the first level that settles the question:

1. The reference page for the exact symbol, including notes and warnings.
2. The type definitions or function signature in the installed package (local, matches the version exactly).
3. The tests of the library in its repository at the tag; tests state intended behaviour.
4. The issue tracker and discussion board: a maintainer's answer outranks a user's guess. Quote and link the comment.
5. Real-world usage via gh_grep, restricted to repositories that pin your version ([gh-grep.md](gh-grep.md)).
6. A minimal experiment in a scratch location ([feasibility-analysis.md](feasibility-analysis.md)).

If still unresolved, report the question as open, with what you tried, rather than guessing.

### Check documentation against behaviour

Documentation can be wrong or stale. For a decisive fact, run a minimal check: call the function with the documented default and print the result, or run the command with `--help` or `--version`. If documentation and behaviour disagree, the installed version's behaviour decides what the code does, and the discrepancy is reported as a finding (with the version and the command). Do not "fix" the project's code to match the documentation until the owner confirms which is right.

### Citing what you found

Every cited fact has: title, URL (to the specific page or anchor), version it applies to, and the date you read it. Quote sparingly (a short phrase) and paraphrase otherwise; never paste long passages, and never paste code from documentation without checking its licence.

Citation line pattern:

```text
<Library> <version> - <page title> - <URL> - read <YYYY-MM-DD> - <what it establishes>
```

Mark a citation that you could not open yourself (second-hand, from a search snippet) as **unverified**.

### Recording and reporting

Put the citations in the `Research` and `Evidence` fields. For a durable pitfall ("version 4 changed the default pool size"), suggest a line for `docs/MEMORY.md` through the coordinator. When the research changes a specification (a constraint, an interface, a data rule), name the doc and its owner under `Docs impact`; the architect updates specification docs, and the implementer updates `README.md` and `CHANGELOG.md`.

## Examples

### Version established first

Bad:

```text
Question: how do I enable retries in the HTTP client?
Answer: set `retries: 3` (from a blog post).
```

Good:

```text
Question: how do I enable retries in HTTP client <Library> as used by this project?
Resolved version: 4.2.1 (lockfile entry; `npm ls <package>` confirms, 2026-11-26).
Source: <Library> 4.x reference, "Retry options" - <URL> - read 2026-11-26.
Finding: retries are configured through `retry.limit` (default 2); the `retries`
key seen in the blog applies to 3.x, removed in 4.0.0 per the 4.0.0 migration guide.
Confidence: high for 4.2.1. Unverified: behaviour on non-idempotent methods (not stated).
```

### Reading a changelog span

```text
Question: does upgrading from 2.3.0 to 2.7.0 change timeout behaviour?
Read: entries 2.4.0, 2.5.0, 2.6.0, 2.7.0 (all between resolved and target version).
Found: 2.5.0 "Changed: default timeout is now 30 s (was none)"; 2.6.0 "Deprecated: `timeout_ms`".
Impact: behaviour changes at 2.5.0 for callers that set no timeout; `timeout_ms` still works
but warns. No Removed entries. Report to the implementer; upgrade itself needs approval.
```

### Documentation versus behaviour

```text
Docs (4.2 reference) say the default of `pool.max` is 10.
Check: printed the resolved config in a scratch script on 4.2.1 -> `pool.max = 5`.
Finding: docs and behaviour disagree for 4.2.1; the changelog for 4.2.0 lists "Changed:
default pool size reduced to 5" without updating the reference page.
Action: reported to the implementer; cited the changelog entry as the decisive source.
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Reading "latest" docs for an older pinned version | The API or default you rely on may not exist | Select the matching version or read the repository at the tag |
| Researching before knowing the resolved version | The answer may be for the wrong major | Read the manifest and lockfile first |
| Trusting a tutorial for a default value | Tutorials omit defaults and age quickly | Confirm in the reference page or the installed source |
| Skipping intermediate release notes in an upgrade | Breaking changes hide in the middle versions | Read every entry between resolved and target version |
| Reaching the "official" site through a search result | Look-alike or stale mirrors rank well | Follow the link from the registry or repository metadata |
| Citing without version and date | The reader cannot tell if it still holds | Use the citation line pattern |
| Treating an Unreleased changelog entry as shipped | The feature may not exist in your version | Check the release tag that contains the entry |
| Changing code to match docs when docs and behaviour differ | Hides a documentation or library defect | Report the discrepancy with the command and version |
| Quoting long passages from the docs | Copying beyond fair use and noise | Paraphrase and link |
| Proposing your own replacement for a removed API | Misses the maintainers' supported path | Use the migration guide's replacement |

## Checklist

- [ ] The resolved version was read from the lockfile or printed by a command, and is written in the report.
- [ ] The documentation site was reached from registry or repository metadata, or marked **unverified**.
- [ ] The pages read match the resolved version (selector, tag or installed source).
- [ ] For version or upgrade questions, every changelog entry between the two versions was read.
- [ ] Deprecations and removals touching the project's usage were listed with the replacement.
- [ ] A decisive fact was confirmed by a command or minimal check, or marked **unverified**.
- [ ] Each citation has title, URL, version and date.
- [ ] Discrepancies between documentation and behaviour are reported, not silently worked around.
- [ ] Durable findings are named for `docs/MEMORY.md` and spec changes for their owners.

## Verify with context7 and gh_grep

- **context7:** resolve the library, then query with the version: `<library> <version> <symbol> parameters and defaults`, `<library> upgrade guide from <old major> to <new major>`, `<library> <version> deprecated <symbol> replacement`. Compare the returned snippet's version with the resolved one, then open the official page it links to. See [context7.md](context7.md).
- **gh_grep:** search for the deprecated or renamed symbol (`<old_symbol>(`) and its replacement (`<new_symbol>(`) to see how maintained projects migrated, and for the exact deprecation message text to find the discussion behind it. Prefer repositories whose lockfile pins your version. See [gh-grep.md](gh-grep.md).

## Sources

- Semantic Versioning 2.0.0: https://semver.org/
- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/
- Diátaxis, start here: https://www.diataxis.fr/start-here/
- Node.js releases (example of a published support policy and release phases): https://nodejs.org/en/about/previous-releases
- Context7 project README (how version-matched documentation is requested): https://github.com/upstash/context7
