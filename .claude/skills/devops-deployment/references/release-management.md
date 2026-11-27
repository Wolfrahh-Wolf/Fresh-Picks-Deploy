# Release Management

Covers semantic versioning, annotated git tags, `CHANGELOG.md` maintenance, pre-release checks and the release workflow; based on SemVer 2.0.0 and Keep a Changelog 1.0.0, checked 2026-11-26.

## Contents

- Semantic versioning rules
- Annotated git tags
- CHANGELOG.md format
- Pre-release checks
- Release workflow

## Guidance

### Semantic versioning rules

Every public release must carry a version number in the form `MAJOR.MINOR.PATCH` per SemVer 2.0.0 (semver.org).

| Segment | Increment when |
|---|---|
| MAJOR | A backwards-incompatible change is made (breaking API change, dropped feature, removed env variable) |
| MINOR | New functionality is added in a backwards-compatible way |
| PATCH | A backwards-compatible bug fix is made |

Pre-release identifiers: `1.0.0-rc.1`, `2.3.0-beta.2`. Build metadata: `1.0.0+build.456` (not part of precedence).

The version in the codebase (e.g. `package.json`, `pyproject.toml`, `Chart.yaml`) is the single source of truth. The git tag must match it exactly.

**Deciding the next version:**
- Look at all commits since the last tag.
- If any `BREAKING CHANGE:` footer or `!` suffix in a commit, MAJOR.
- If any `feat:` commit, MINOR.
- If only `fix:`, `chore:`, `docs:` etc., PATCH.
- Use Conventional Commits (see `git-version-control` skill) consistently so this determination can be automated.

### Annotated git tags

Always use **annotated** tags, not lightweight tags. Annotated tags include the tagger identity, date and a message; they are proper Git objects and are picked up by `git describe`.

```bash
# Bump version in manifest first, commit, then tag
npm version 1.2.3 --no-git-tag-version   # or edit pyproject.toml
git add package.json
git commit -m "chore: release v1.2.3"
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin main --follow-tags
```

`--follow-tags` pushes all annotated tags reachable from the current branch. Never push tags with `git push --tags` as it pushes every local tag including drafts.

Tag naming convention: `v` prefix followed by the full SemVer string — `v1.2.3`, `v2.0.0-rc.1`.

Deleting or moving a published tag is a breaking contract with consumers who may have pinned it. If a release is incorrect, publish a corrected `PATCH` release; do not delete the tag.

### CHANGELOG.md format

Maintain `CHANGELOG.md` at the repository root. Owner: implementer (per `AGENTS.md`). Format: Keep a Changelog 1.0.0.

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.3] - 2026-11-26

### Added
- POST /orders now accepts an `Idempotency-Key` header.

### Fixed
- Pagination cursor was incorrectly reset on filter changes.

### Security
- Upgraded `express` to 4.21.1 to patch CVE-XXXX-XXXX.

## [1.2.2] - 2026-11-01
...
```

Sections per release (use only what applies): `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

**Update rules:**
- Add entries to `[Unreleased]` as changes land on `main`.
- When cutting a release, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and add a fresh empty `[Unreleased]` above it.
- Every public API change, security fix and breaking change must have a `CHANGELOG.md` entry.

### Pre-release checks

Run all of these before creating the release tag:

| Check | Command / action |
|---|---|
| All tests pass | Run the full test suite in CI on the release branch |
| Lint clean | Lint passes with 0 errors |
| Image builds | `docker build` succeeds |
| Image scan | `trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed` passes |
| Version bumped | Manifest version (`package.json`, `pyproject.toml`) matches the intended tag |
| `CHANGELOG.md` updated | `[Unreleased]` section renamed; new entry contains all changes |
| Staging deploy verified | The release candidate has been deployed to staging and smoke-tested |
| No open CRITICAL/HIGH issues | Reviewer and security-auditor have no unresolved findings for this release |

Do not tag the release until all checks pass. Tag from `main` (or the release branch) only after the merge to that branch is complete.

### Release workflow

A GitHub Actions workflow triggered by `workflow_dispatch` with an explicit version input:

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Release version (e.g. 1.2.3)'
        required: true

permissions: {}

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
        with:
          fetch-depth: 0

      - name: Verify version matches manifest
        run: |
          MANIFEST_VERSION=$(node -p "require('./package.json').version")
          if [ "$MANIFEST_VERSION" != "${{ inputs.version }}" ]; then
            echo "Manifest version $MANIFEST_VERSION != input ${{ inputs.version }}"
            exit 1
          fi

      - name: Create annotated tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -a "v${{ inputs.version }}" -m "Release v${{ inputs.version }}"
          git push origin "v${{ inputs.version }}"

      - name: Create GitHub Release
        uses: softprops/action-gh-release@e7a8f85e1c67a31e6ed99a94b41bd0b71bbee6b8  # v2.0.9
        with:
          tag_name: v${{ inputs.version }}
          generate_release_notes: true
          draft: false
```

`generate_release_notes: true` automatically generates release notes from merged pull requests since the previous tag, using the PR titles and labels.

> ⚠️ Pushing a tag and publishing a release requires user approval first per `AGENTS.md` Approval gates. Run all pre-release checks before triggering this workflow.

## Examples

### Deciding the version bump from commits

```
feat: add cursor-based pagination to /orders          → MINOR (new feature)
fix: correct status code on empty list from 404 to 200 → PATCH (bug fix)
feat!: remove /v1/orders; use /v2/orders              → MAJOR (breaking change)

BREAKING CHANGE: footer also triggers MAJOR regardless of type prefix
```

### Automated version bump with npm

```bash
# Patch: 1.2.3 → 1.2.4
npm version patch --no-git-tag-version

# Minor: 1.2.3 → 1.3.0
npm version minor --no-git-tag-version

# Major: 1.2.3 → 2.0.0
npm version major --no-git-tag-version
```

The `--no-git-tag-version` flag prevents npm from also creating a tag (do that manually with annotation).

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using lightweight tags (`git tag v1.2.3` without `-a`) | No tagger identity, date or message; not picked up correctly by `git describe` and some release tools | Always use `git tag -a v1.2.3 -m "Release v1.2.3"` |
| Tagging before updating the version in the manifest | Tag and code version disagree; generated clients or SDKs embed the wrong version | Bump the manifest, commit, then tag |
| Publishing to production without a staging verification step | First deploy of a build is to production; there is no safety net | Always deploy to staging, run smoke tests, then promote to production |
| Deleting or force-moving a published tag | Consumers who pinned the tag now point to different or no code | Never mutate a published tag; publish a new patch release for fixes |
| Forgetting to update `CHANGELOG.md` before the release | Release notes are absent; users cannot tell what changed | Update `[Unreleased]` as changes land; rename the section at release time |

## Checklist

- [ ] Version in the manifest (`package.json`, `pyproject.toml`) bumped following SemVer rules.
- [ ] `CHANGELOG.md` `[Unreleased]` section renamed to `[X.Y.Z] - YYYY-MM-DD`.
- [ ] Annotated tag created (`git tag -a vX.Y.Z -m "..."`) from `main`.
- [ ] All CI checks (tests, lint, image scan) passed on the commit being tagged.
- [ ] Staging deploy of this exact image verified with a smoke test.
- [ ] GitHub Release created with generated or manually written release notes.
- [ ] `CHANGELOG.md` committed and pushed before the tag.

## Verify with context7 and gh_grep

- **context7:** Resolve `softprops/action-gh-release` SHA for the latest release. Check `generate_release_notes`, `draft` and `tag_name` input options. For Node.js projects, check `npm version` subcommands.
- **gh_grep:** Search `git tag -a` with `-m "Release` for annotated tag conventions; `generate_release_notes: true` for GitHub Release note automation; `workflow_dispatch` with `inputs: version:` for manual release trigger patterns.

## Sources

- Semantic Versioning 2.0.0: https://semver.org/spec/v2.0.0.html
- Keep a Changelog 1.0.0: https://keepachangelog.com/en/1.0.0/
- GitHub Releases documentation: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
- softprops/action-gh-release: https://github.com/softprops/action-gh-release
