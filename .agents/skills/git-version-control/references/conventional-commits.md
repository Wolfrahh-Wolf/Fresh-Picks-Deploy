# Conventional Commits

How to write, review and fix commit messages under the Conventional Commits 1.0.0 specification, including types, scopes, breaking changes, reverts and squash subjects; assumes Conventional Commits 1.0.0 and Git 2.x, checked 2026-11-27. A project's own commit-lint configuration overrides the defaults below.

## Contents

- The format
- The rules, in plain terms
- Choosing the type
- Choosing the scope
- Writing the description, body and footers
- Breaking changes
- Reverts
- Commit hygiene: atomic, buildable, clean
- Squash merges and the final subject
- Fixing a wrong message
- Writing messages from PowerShell

## Guidance

### The format

```text
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

The prefix is a type, an optional scope in parentheses, an optional `!`, then a colon and one space. The description follows immediately. A body may follow after one blank line, and footers after one more blank line.

### The rules, in plain terms

The specification's sixteen rules reduce to these, with the spec's own MUST and MAY strength:

| # | Rule | Strength |
|---|---|---|
| 1 | The commit begins with a type, then optional scope, optional `!`, then a colon and a space | MUST |
| 2 | `feat` is used when the commit adds a feature to the application or library | MUST |
| 3 | `fix` is used when the commit fixes a bug | MUST |
| 4 | A scope is a noun in parentheses describing a section of the codebase, for example `fix(parser):` | MAY, and if present MUST be a noun in parentheses |
| 5 | The description follows the colon and space immediately | MUST |
| 6 | A body begins one blank line after the description | MAY, and MUST start after a blank line |
| 7 | The body is free-form and may have several paragraphs | MAY |
| 8 | Footers follow one blank line after the body; each is a word token, then `: ` or ` #`, then a value | MAY |
| 9 | Footer tokens replace spaces with `-` (for example `Acked-by`); `BREAKING CHANGE` is the one exception | MUST |
| 10 | Footer values may contain spaces and newlines; parsing ends at the next valid token and separator | MAY |
| 11 | A breaking change is indicated in the prefix or as a footer | MUST |
| 12 | A breaking-change footer is uppercase `BREAKING CHANGE`, a colon, a space and a description | MUST |
| 13 | In the prefix, a breaking change is `!` immediately before the colon; the footer may then be omitted and the description describes the change | MUST |
| 14 | Types other than `feat` and `fix` are allowed | MAY |
| 15 | Tools must not treat the parts as case-sensitive, except `BREAKING CHANGE` which is uppercase | MUST NOT |
| 16 | `BREAKING-CHANGE` as a footer token is a synonym for `BREAKING CHANGE` | MUST |

Semantic Versioning mapping, from the specification: `fix` corresponds to a PATCH release, `feat` to a MINOR release, and a breaking change of any type to a MAJOR release. Other types carry no implicit version effect unless they are breaking. Deciding and publishing the version is a release task; writing the changelog entry from these commits is `technical-documentation`'s job.

### Choosing the type

The specification mandates only `feat` and `fix`. The widely used extended set is the one recommended by `@commitlint/config-conventional` (Angular convention), which the specification page cites. Use these unless the project defines others:

| Type | Use for | Version effect |
|---|---|---|
| `feat` | A new capability users or callers can use | MINOR |
| `fix` | A bug fix | PATCH |
| `perf` | A change whose purpose is performance | none, unless breaking |
| `refactor` | A code change that neither fixes a bug nor adds a feature | none |
| `docs` | Documentation only | none |
| `test` | Adding or correcting tests only | none |
| `build` | Build system or dependency changes | none |
| `ci` | CI configuration and scripts | none |
| `style` | Formatting with no behaviour change (whitespace, semicolons) | none |
| `chore` | Maintenance that fits nowhere else | none |
| `revert` | Reverting an earlier commit | per the reverted change |

How to decide:

1. Ask what a user, caller or operator observes. If a bug goes away: `fix`. If something new is possible: `feat`. If nothing observable changes: `refactor`, `test`, `docs`, `build`, `ci`, `style` or `chore`.
2. A fix to a test file is `test`; a fix to production code found by a test is `fix`.
3. A dependency upgrade is `build` (or `fix` when it resolves a vulnerability or defect that users hit, with the reason in the body). A major upgrade needs approval first (see `AGENTS.md`).
4. If one change spans two types (a feature and an unrelated fix), split it into two commits. The specification's own guidance is to split the work into multiple commits where possible.
5. If a type is wrong, fix it before merging (see "Fixing a wrong message"). A type outside the specification is not catastrophic; spec-based tools simply skip it.

Use lowercase types. The specification does not require it, but consistency matters and most lint configurations expect lowercase.

### Choosing the scope

A scope is a noun naming the part of the codebase affected: `feat(auth):`, `fix(parser):`, `docs(api):`.

- Take scopes from the project's list if it has one (commit-lint configuration, `CONTRIBUTING`, or the existing history: `git log --format=%s -50`). Do not invent a new scope when an existing one fits.
- Use a stable component name (module, package, service, area), never a file name, a task id or a person.
- Omit the scope when the change is cross-cutting or the project does not use scopes. An absent scope is better than a vague one.
- One scope per commit. If you need two, the commit probably holds two changes.

### Writing the description, body and footers

**Description** (the part after the colon):

- Imperative mood and present tense: "add", "fix", "remove", not "added" or "adds".
- Lowercase first word unless it is a proper noun or symbol; no trailing full stop.
- Say what the change does, not how or why. Be specific: "reject login after 5 failed attempts", not "update login".
- Keep the whole first line within about 72 characters, so it displays fully in logs and as a pull request title. The specification sets no length; this is a common convention, so follow the project's limit if it has one.
- Never include a ticket id as the only content, and never include secrets or personal data.

**Body** (optional; use it whenever the reason is not obvious):

- Explain **why** the change is needed, what constraint or defect drove it, and any trade-off or alternative you rejected. The diff already shows what changed.
- Wrap lines at about 72 characters. Separate paragraphs with a blank line.
- Describe behaviour a reviewer cannot infer: migration steps, an ordering requirement, a performance consequence.

**Footers** (optional): a token and a value, one per line.

```text
Refs: #123
Closes: #456
Reviewed-by: <name>
BREAKING CHANGE: <what breaks and what to do instead>
```

Use `Refs` for related work and a closing keyword only if the project and hosting platform use closing keywords on merge. Never put a secret, token or private URL in a footer.

### Breaking changes

A breaking change is any change that requires callers or operators to change something: a removed or renamed public API, a changed default, a changed data format, a dropped runtime version, a database change that needs action. Mark it in at least one of two ways; marking both is allowed and recommended for clarity:

```text
feat(api)!: remove the v1 /orders endpoint

BREAKING CHANGE: clients must call /v2/orders; /v1/orders now returns 410 Gone.
```

- `!` goes immediately before the colon, after the scope if there is one.
- The footer is `BREAKING CHANGE:` in uppercase (or the synonym `BREAKING-CHANGE:`), then a description that says what breaks and the migration path.
- A breaking change in any type, including `fix` and `refactor`, means a MAJOR version bump under Semantic Versioning, so decide deliberately. If you doubt that a change is breaking, treat it as breaking and say why in the body, then flag it to the coordinator.
- Breaking changes need a `CHANGELOG.md` entry and usually a documentation update; list both in `Docs impact`.

### Reverts

The specification does not define revert behaviour and leaves it to tooling. The convention it suggests is a `revert` type and a footer that references the reverted commits:

```text
revert: remove rate limiter from login route

This reverts commit 676104e because it blocked legitimate retries behind a shared proxy.

Refs: 676104e, a215868
```

`git revert <commit>` records a new commit that undoes an earlier one and opens an editor for the message; its manual strongly recommends explaining **why** the commit is being reverted and warns that repeated reverts produce unwieldy subjects such as `Reapply "Reapply "..."`. Reverting a published commit is the safe alternative to rewriting history; it is still a Tier 3 action once pushed. See `merge-rebase.md` for reverting a merge commit, which needs `-m`.

### Commit hygiene: atomic, buildable, clean

| Rule | Reason | Check |
|---|---|---|
| One logical change per commit | Easy to review, revert and bisect | The message needs no "and also" |
| Every commit builds and passes the tests it touches | `git bisect` can land on any commit | Run tests at each commit when feasible, at least at the tip |
| Tests and the code they cover ship together | A revert should not leave orphans | `git show --stat <commit>` lists both |
| No unrelated formatting changes | They bury the real change | Review `git diff --cached` |
| No debug output, commented-out code, secrets, `.env` files or build artefacts | They persist in history for ever | Scan the staged diff; use `.env.example` for names |
| No "WIP", "fix typo", "address review" commits in the final history | They carry no information | Use `git commit --fixup=<commit>` and an approved autosquash before merge, or let a squash merge collapse them |
| Stage by path | `git add -A` sweeps in stray files | `git add <path>...` then `git diff --cached --stat` |

Do not skip hooks with `--no-verify`, do not disable signing, and do not change `user.name` or `user.email` configuration. A failing hook is information to report.

### Squash merges and the final subject

When the project squashes pull requests, the squash commit is what stays in history. The specification's FAQ notes that contributors need not follow it on every intermediate commit if maintainers rewrite the message at squash time. Therefore:

- Make the **pull request title** a valid Conventional Commits subject (`type(scope): description`); it is usually the squash subject.
- Make the pull request body carry the commit body and footers, including `BREAKING CHANGE:`.
- With the CLI, the merge subject and body can be set explicitly (`gh pr merge --squash --subject ... --body-file ...`); see `github-cli.md`. Merging is a Tier 3 action.
- If the project preserves individual commits (merge commit or rebase merge), every commit in the branch must already be valid.

### Fixing a wrong message

| Situation | Action | Tier |
|---|---|---|
| Not committed yet | Write it correctly | n/a |
| Last commit, not pushed | `git commit --amend` (rewrites the commit) | 2 |
| Older unpushed commits | `git rebase -i <base>` with `reword` | 2 |
| Pushed, on your own branch, others have not pulled | Rewrite, then `--force-with-lease` push | 2 and 3, see `merge-rebase.md` |
| Pushed to a shared or protected branch | Leave it; correct it in the pull request squash subject or with a follow-up commit | 3 |

Back up first (`git branch backup/<name>`), and ask before rewriting. Messages cannot be edited in place; "changing" one creates a new commit with a new hash.

### Writing messages from PowerShell

Avoid inline quoting problems by writing the message to a file and committing with `-F`. A single-quoted here-string keeps `$`, backticks and quotes literal; the closing `'@` must start at the beginning of its line:

```powershell
$msg = @'
fix(auth): reject login after 5 failed attempts

The counter was reset on every request, so the limit never triggered.
Count attempts per IP in a rolling 60-second window.

Refs: #123
'@
Set-Content -Path "$env:TEMP\commitmsg.txt" -Value $msg -Encoding utf8
git commit -F "$env:TEMP\commitmsg.txt"
Remove-Item "$env:TEMP\commitmsg.txt"
```

Encoding note (unverified): Windows PowerShell 5.1's `-Encoding utf8` writes a byte order mark, which can show up in the commit message; PowerShell 7 writes UTF-8 without one. Check with `git log -1 --format=%B`, or write the file with an editor or from PowerShell 7.

For a one-line message, single quotes avoid expansion: `git commit -m 'fix(auth): reject login after 5 failed attempts'`. A single quote inside the message is doubled: `'don''t'`.

## Examples

### Bad to good: descriptions

```text
Bad:   update stuff
Bad:   Fixed the bug.
Bad:   feat: Added new login page and fixed header and updated deps
Good:  fix(auth): reject login after 5 failed attempts
Good:  feat(search): add fuzzy matching for product names
Good:  refactor(billing): extract tax calculation into its own module
Good:  build: pin the base image to a digest
```

The third bad example mixes three changes and three types; split it into `feat(auth)`, `fix(ui)` and `build` commits.

### Full message with a body and footers

```text
fix(session): load the session after the write is acknowledged

The read ran against a replica that had not yet received the write, so
login failed for about 2% of requests under load. Wait for the write
acknowledgement before loading, and add a regression test that reads
immediately after writing.

Refs: #214
```

### Breaking change with migration note

```text
feat(config)!: require STORE_URL instead of SESSION_URL

BREAKING CHANGE: the SESSION_URL variable is no longer read. Rename it to
STORE_URL in every environment and in .env.example before upgrading.
```

### Docs and chore examples

```text
docs(api): document the 429 response for POST /login
chore: remove unused lint rule
test(auth): cover lockout after 5 failed attempts
ci: cache the dependency directory between runs
```

### Reviewing a history

```bash
git log --format='%h %s' origin/main..HEAD
```

Every line should match `type(scope)!?: description`. Anything that does not is fixed before the pull request is opened (a Tier 2 action).

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| A vague description ("update", "fix stuff") | Useless in logs, bisect and changelogs | Say what the change does, specifically |
| Past tense or a trailing full stop | Inconsistent history; some lint rules reject it | Imperative, no final full stop |
| Mixing a feature and a fix in one commit | One type cannot describe it; hard to revert | Split into commits by purpose |
| Marking `feat` for a refactor, or `fix` for a feature | Wrong version bump in tools that read types | Decide by observable behaviour |
| Hiding a breaking change in the body only | Tools and readers miss it | Use `!` or an uppercase `BREAKING CHANGE:` footer |
| Lowercase `breaking change:` footer | The spec requires uppercase | Write `BREAKING CHANGE:` |
| Scope as a file name or task id | Scopes become noise | Use a stable component name |
| Putting a secret or personal data in a message | History is permanent and widely copied | Never; if it happens, stop and report |
| `--no-verify` to get past a failing hook | Hides the problem and breaks the gate | Fix the cause or report it |
| Inline multi-line message in PowerShell with backticks or `$` | The shell expands or mangles it | Use `-F` with a file from a single-quoted here-string |
| Rewriting pushed commits to fix a message | Breaks others' clones | Fix it in the squash subject or a follow-up commit |

## Checklist

- [ ] The first line matches `type(scope)!?: description`, with a lowercase type from the project's list.
- [ ] The description is imperative, specific and within the project's length limit.
- [ ] The commit holds one logical change with one type.
- [ ] A body explains why when the reason is not obvious.
- [ ] Any breaking change has `!` or an uppercase `BREAKING CHANGE:` footer with a migration note.
- [ ] Footers use valid tokens (`Refs`, `Closes`, `BREAKING CHANGE`) and contain no secrets.
- [ ] The staged diff was read; no unrelated changes, debug output or secret-like strings.
- [ ] Tests for the change are in the same commit or the same pull request.
- [ ] Hooks and signing were not bypassed.
- [ ] The pull request title is a valid subject if the project squashes.

## Verify with context7 and gh_grep

- **context7:** Check the commit-lint tooling the project actually uses at its locked version: the shared config's allowed types, the header length rule, the scope rule and how it treats case. Queries: "commitlint config-conventional type-enum", "commitlint header-max-length default", "git commit --fixup --amend autosquash".
- **gh_grep:** Search for real configurations and examples: the literal strings `type-enum`, `scope-enum`, `BREAKING CHANGE:` in commit-message tests, and `commitlint.config` files in comparable repositories, to learn which scopes projects of this kind use.

## Sources

- Conventional Commits 1.0.0 specification (the maintained copy of the specification text): https://raw.githubusercontent.com/conventional-commits/conventionalcommits.org/refs/heads/master/content/v1.0.0/index.md
- git-revert manual (last updated in Git 2.54.0): https://git-scm.com/docs/git-revert.html
- git-rebase manual (last updated in Git 2.54.0), for `--autosquash` and `fixup`: https://git-scm.com/docs/git-rebase.html
- gh pr merge manual: https://cli.github.com/manual/gh_pr_merge
- Microsoft Learn, about_Quoting_Rules (PowerShell 7.6 documentation): https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_quoting_rules
