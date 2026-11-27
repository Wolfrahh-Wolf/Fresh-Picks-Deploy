# Changelog

How to write `CHANGELOG.md` entries, categorise them, prepare release sections and mark breaking changes; assumes Keep a Changelog 1.1.0 (pinned by the RelayCrew template) and 2.0.0 (published June 2026), and Semantic Versioning 2.0.0, all read on 2026-11-26. The project's existing changelog style wins over these defaults.

## Contents

- Ownership and purpose
- Which Keep a Changelog version
- File structure
- Entry style
- The six categories
- What not to record
- Breaking changes and deprecations
- Versions and Semantic Versioning
- Preparing a release section
- Yanked releases, corrections and security entries
- Automation, release notes and large changelogs

## Guidance

### Ownership and purpose

The implementer owns `CHANGELOG.md`. A changelog is for humans: a curated record of the notable differences between versions. It is not a commit log. Commits describe steps in how the code evolved. A changelog entry describes a difference a user or operator can notice. Commit message conventions belong to `git-version-control`.

Add an entry in the same change that causes it. The architect does not edit the changelog. If a specification change needs an entry, the architect names it in `Docs impact` for the implementer.

### Which Keep a Changelog version

The RelayCrew template links Keep a Changelog 1.1.0, and Keep a Changelog 2.0.0 is now published as well. Both define the same six change types, `YYYY-MM-DD` dates, an `Unreleased` section at the top, a stated versioning scheme, and the `[YANKED]` marker. Version 2.0.0 adds guidance on structure, release notes, automation, scale and optional per-release summaries.

- Keep the link the project already pins. Do not change the preamble link on your own.
- The practices in this file are valid under both versions.
- If the user wants 2.0.0, update the preamble link on request and report it.

### File structure

~~~~markdown
# Changelog

Format follows Keep a Changelog. Versions follow Semantic Versioning.

## [Unreleased]

### Added

## [1.2.0] - 2026-03-04

### Added

[Unreleased]: https://github.com/<owner>/<repo>/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/<owner>/<repo>/compare/v1.1.0...v1.2.0
~~~~

Rules:

1. `## [Unreleased]` is first. Newest released version follows, then older ones in descending order.
2. Each released heading is `## [x.y.z] - YYYY-MM-DD`. The date is the release date in ISO 8601.
3. Under a version, use only these headings, in this order: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. The template's `Unreleased` section lists `Added`, `Changed`, `Fixed`, `Security`. Add `Deprecated` and `Removed` when you need them. Delete empty headings from released sections.
4. Version headings are link references. The links sit at the bottom: `[Unreleased]` compares the latest tag with `HEAD`, each version compares with the previous one, and the oldest links to its own tag. Match the project's tag naming by listing the existing tags, which is a read-only check.
5. A project without version numbers keeps dated entries under `Unreleased`.
6. The preamble states the versioning scheme. Keep it.

### Entry style

An entry says what changed from the reader's side, in plain words a non-native speaker can follow.

1. One sentence, two at most. Group related edits into one entry.
2. Name the interface in code font: the command, flag, endpoint, option, config key or file.
3. Lead with the effect, not the implementation. "Login no longer fails when the email contains a plus sign", not "Fixed regex in `validateEmail`".
4. Add the reason or impact only when it is not obvious, in a short clause.
5. Say who is affected when only some users are: a platform, a plan, a config.
6. Link an issue or pull request only if the project does so. Collect such links as references at the bottom of the file. Repositories move and links break, so the sentence must stand without the link.
7. No commit hashes, author names, ticket jargon or internal module names.
8. Match the tense and phrasing already used in the file. Be consistent inside a release.
9. Write it so the entry would still be correct and clear a year later.

### The six categories

| Category | Use for | Decision test |
|---|---|---|
| Added | New features, endpoints, commands, options, configuration keys | Was this impossible before? |
| Changed | Intentional changes to existing behaviour, defaults, output, supported runtime minimums | Did we choose to make it different? |
| Deprecated | Features that still work but will be removed | Does it still work, with a planned end? Name the removal version |
| Removed | Features that are now gone | Did it stop existing? |
| Fixed | Corrections of behaviour that was wrong | Was the old behaviour a bug? |
| Security | Fixes for vulnerabilities | Was it a vulnerability? |

When unsure between `Changed` and `Fixed`: `Fixed` means the behaviour was wrong, `Changed` means the behaviour was right by design and the design changed. A fix that breaks clients who relied on the wrong behaviour is both: record it under `Fixed` and mark it `**Breaking:**`.

### What not to record

- Refactors, renames of internals, test-only changes, formatting changes and CI tweaks with no effect on users or operators.
- Documentation edits, unless they correct documented behaviour users depend on.
- Dependency bumps with no visible effect. Do record a bump that changes the supported runtime, a default or a behaviour.
- Work in progress that is not reachable by a user.

If the answer to "would a user or operator notice?" is no, write no entry. Record that as `no change` for the changelog with the reason.

### Breaking changes and deprecations

A breaking change is one that makes existing users, scripts, integrations or stored data stop working without their action. Typical examples are a removed or renamed command, endpoint or option, a changed default that alters results, a required new configuration, a changed file or response format, a raised minimum runtime.

1. Put it under `Changed` or `Removed` (or `Fixed` when a fix breaks reliance on the old behaviour). Do not create a separate section.
2. Start the entry with `**Breaking:**`.
3. Say what breaks, name the stable interface it affects (command line, library API, protocol, file format or configuration schema), and give the migration in one line. If the migration needs more than a few lines, link a migration guide.
4. Deprecate before removing. Mark `Deprecated` in one release, naming the replacement and the version that will remove it, and record `Removed` in the later release. Semantic Versioning asks for the deprecation to ship in at least one minor release before removal in a major release.
5. Mention the same change in the documentation it touches: the README, the contract entry's Compatibility notes. See [docs-sync.md](docs-sync.md).

### Versions and Semantic Versioning

Semantic Versioning 2.0.0 rules, summarised:

| Bump | When |
|---|---|
| MAJOR | Incompatible public API changes. Resets MINOR and PATCH to 0 |
| MINOR | Backward-compatible new functionality, or when public functionality is deprecated. Resets PATCH to 0 |
| PATCH | Backward-compatible bug fixes |

Further rules: versions `0.y.z` are for initial development and anything may change. A pre-release is a hyphen and dot-separated identifiers, for example `1.0.0-alpha.1`, and sorts lower than the release. Build metadata after `+` does not affect precedence. Once released, the contents of a version must not change. Fix forward with a new version.

How to propose a number from the entries in `Unreleased`: any `**Breaking:**` entry points to MAJOR (for `0.y.z` follow the project's stated policy); otherwise any `Added` or `Deprecated` entry points to MINOR; only `Fixed` and `Security` fixes point to PATCH. This is a proposal. The user decides the version. What the public API is for this project is the project's call, so ask if unclear.

### Preparing a release section

Do this only when the brief asks for it. It edits the file. It does not release anything.

1. Confirm the version number with the coordinator.
2. Take the date from the system clock. Do not guess it. POSIX shells: `date +%F`. PowerShell: `Get-Date -Format yyyy-MM-dd`.
3. Rename `## [Unreleased]` to `## [x.y.z] - YYYY-MM-DD`. Delete empty category headings.
4. Add a new empty `## [Unreleased]` section above it with the template's headings.
5. Optional: when the release deserves an introduction, open the section with a short summary of its theme or its most important change, before the category headings. Skip it otherwise.
6. Update the link references at the bottom: add the new version's comparison and repoint `[Unreleased]` to compare the new tag with `HEAD`.
7. Review the section for entries that are internal-only, duplicated or unclear.
8. Stop. Creating a tag, pushing, publishing a package, or creating a hosted release page is a gated action. It needs the user's approval for that exact action and target. For the release procedure load `devops-deployment`. For tags and pushes load `git-version-control`.

### Yanked releases, corrections and security entries

- **Yanked.** A release pulled for a serious bug or security problem stays in the file, marked `## [x.y.z] - YYYY-MM-DD [YANKED]`. Add a short line under it saying what to use instead.
- **Corrections.** Do not rewrite released sections. Correct a factual error only, minimally, and report the correction in `Docs impact` with what was wrong.
- **Security entries.** State what was fixed, which versions are affected and how to upgrade. Do not include exploit details. Whether and when to disclose is the user's decision, so write the entry locally and do not push or publish it. Auditing the vulnerability belongs to `security-engineering`.

### Automation, release notes and large changelogs

- **Existing tooling wins.** If the project generates changelog content from commits or change files (for example with Conventional Commits tooling, release-please, Changesets or git-cliff), follow the project's workflow and do not hand-edit text the tool will overwrite. Treat any generated or model-drafted text as a draft: check each entry is true, relevant to users and correctly categorised. Machines can draft and people curate.
- **Do not turn the changelog into a required check** in CI on your own. Contributors then add filler to pass it. Mechanical steps such as moving `Unreleased` into a dated version are better automated than the content.
- **Release notes.** The changelog is the record. Release notes announce one release and are written from it. When asked for release notes, extract the version's section by its heading and adapt it. Do not maintain two separate sources. Notes generated by a hosting platform live outside the repository, so treat them as drafts.
- **Size.** One file is usually fine. If it becomes unwieldy, move old versions to archive files that link back and forth with the main file, and never delete entries.
- **Several components.** Unrelated projects keep their own changelogs. A single product built from components may have per-component changelogs and one central changelog that summarises each release for readers.

## Examples

### Bad to good entries

~~~~markdown
Bad:
- Fixed bug
- Refactored auth module (#412)
- Updated deps
- Changed the thing with the config

Good:
### Fixed
- Login no longer fails when the email address contains a plus sign.

### Changed
- **Breaking:** `PORT` now defaults to `8080` instead of `3000`. Set `PORT=3000` to keep the old behaviour.
~~~~

### Filled-in changelog

~~~~markdown
# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `POST /api/auth/login` endpoint. Returns an access token that expires after 15 minutes.

### Deprecated

- `GET /api/login`. Use `POST /api/auth/login`. It will be removed in 3.0.0.

## [2.1.0] - 2026-05-12

### Added

- `--dry-run` option for the `import` command. It prints what would change and writes nothing.

### Fixed

- `import` no longer stops with an error when the input file has a byte-order mark.

## [2.0.0] - 2026-03-02

### Changed

- **Breaking:** The configuration file is now `app.config.json` instead of `config.json`. Rename your file. The old name is no longer read.

### Removed

- **Breaking:** The `--legacy-format` option. Convert input files to the current format first.

### Security

- Session tokens are now invalidated when the password changes. Affects all 1.x releases. Upgrade to 2.0.0 or later.

## [1.0.1] - 2026-01-20 [YANKED]

### Fixed

- Corrected the retry delay calculation. This release crashes on start. Use 1.0.2.

[Unreleased]: https://github.com/<owner>/<repo>/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/<owner>/<repo>/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/<owner>/<repo>/compare/v1.0.1...v2.0.0
[1.0.1]: https://github.com/<owner>/<repo>/releases/tag/v1.0.1
~~~~

The names, versions and dates above are illustrative. The `<owner>` and `<repo>` values are placeholders.

### Deprecation lifecycle

~~~~markdown
## [2.4.0] - 2026-06-01
### Deprecated
- `GET /api/login`. Use `POST /api/auth/login`. It will be removed in 3.0.0.

## [3.0.0] - 2026-09-15
### Removed
- **Breaking:** `GET /api/login`. Use `POST /api/auth/login`.
~~~~

### Release preparation record (goes in Evidence)

~~~~text
Release section prepared for 2.2.0 (user confirmed number).
Date from system clock: 2026-07-01.
Unreleased renamed; new empty Unreleased added; link references updated.
Tags checked (read-only): existing tags use the "v" prefix.
Not done: tag, push, publish (need user approval).
~~~~

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Pasting the commit log | Noisy, written for developers | Write curated entries from the user's side |
| Entries such as "Fixed bug" or "Updated deps" | Tell the reader nothing | Name the interface and the effect |
| Hiding a breaking change inside `Changed` with no marker | Users upgrade and break | Prefix `**Breaking:**` and give the migration |
| Removing a feature with no earlier `Deprecated` entry | Users get no warning | Deprecate in a minor release, remove in a later major |
| Guessing the date | Wrong history, hard to correct | Take it from the system clock, ISO 8601 |
| Rewriting a released section | History becomes untrustworthy | Fix factual errors only, report them |
| Inventing categories like "Improvements" | Breaks the convention and tools | Use the six categories |
| Recording internal refactors | Buries notable changes | Record only what users or operators can notice |
| Exploit details in a `Security` entry | Helps attackers before users can upgrade | Say what was fixed and how to upgrade |
| Tagging or pushing as part of "preparing the release" | Releasing is gated | Edit the file, stop, ask for approval |
| Forgetting the link references | Version headings no longer link | Update the comparison links with each release |

## Checklist

- [ ] The file starts with the preamble and `## [Unreleased]`, and versions run newest to oldest.
- [ ] Every user-visible or operator-visible change in this task has one entry under `Unreleased`, or the report says why none is needed.
- [ ] Every entry sits under exactly one of the six categories.
- [ ] Every entry names the interface and states the effect.
- [ ] Every breaking change starts with `**Breaking:**` and states what breaks and the migration.
- [ ] Every removal has an earlier `Deprecated` entry, or the report says why not.
- [ ] Every released heading has a `YYYY-MM-DD` date taken from the system clock.
- [ ] No released section was rewritten except for a reported factual correction.
- [ ] Link references at the bottom match the headings and the project's tag names.
- [ ] No exploit details, secrets or internal hostnames appear.
- [ ] No tag, push or publish was performed without recorded approval.
- [ ] Generated or model-drafted text was checked line by line.

## Verify with context7 and gh_grep

- **context7:** if the project uses release or changelog tooling, query its documentation at the version in the lockfile, for example `release-please changelog sections configuration`, `changesets changelog format`, `git-cliff configuration template` and `semantic-release changelog plugin`. Confirm the current Keep a Changelog version and the Semantic Versioning rules in the official sources listed below.
- **gh_grep:** search literal text to see real changelogs, for example `## [Unreleased]`, `**Breaking:**`, `[Unreleased]: https://github.com/` and `### Deprecated` in `CHANGELOG.md` files. Prefer the Keep a Changelog documentation when a repository differs.

## Sources

- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/
- Keep a Changelog 2.0.0: https://keepachangelog.com/en/2.0.0/
- Semantic Versioning 2.0.0: https://semver.org/
