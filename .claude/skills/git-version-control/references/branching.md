# Branching

How to choose a branching model, name and size branches, run parallel work without collisions, and work within branch protection; assumes Git 2.x (manuals checked at 2.52 to 2.56) and GitHub, checked 2026-11-27. The project's own `AGENTS.md` and contribution rules win over anything here.

## Contents

- Choosing a model
- Trunk-based development with short-lived branches
- Feature branches and GitHub flow
- What to avoid: long-lived branches
- Naming branches
- Branch lifetime, size and integration
- Parallel work and worktrees
- Branch protection: what it blocks and what you must not touch
- Creating, updating and deleting branches safely

## Guidance

### Choosing a model

Use the model the project already uses; read `AGENTS.md`, `CONTRIBUTING`, the default branch's recent history and any branch-protection note before you create anything. If nothing is defined, default to **short-lived feature branches merged into one trunk through pull requests** (GitHub flow). That is trunk-based development with a review gate, and it matches the safety gates in `AGENTS.md`.

| Model | Shape | Fits when | Cost |
|---|---|---|---|
| Direct to trunk | Commit to the default branch, small and often | A very small, trusted team with strong automated checks | No review gate; not usable here, because agents never commit to the default branch |
| Short-lived feature branches | Branch from trunk, merge back within a day or two | Most teams, and every agent-driven project | Needs fast review and small changes |
| GitHub flow | The same, with the pull request as the unit of review and merge | Projects hosted on GitHub that deploy from the default branch | Same as above |
| Release branches | A branch per supported release, only fixes cherry-picked in | Several supported versions at once | Extra merge work; use only if the project already supports multiple versions |
| Long-lived integration branches (for example develop plus release plus hotfix) | Parallel permanent branches | Rare; scheduled, versioned products with heavy release ceremony | Painful merges, stale branches, hidden integration risk |

Do not introduce a model change in a task. If the current model looks wrong, report it as a follow-up for the coordinator and the user.

### Trunk-based development with short-lived branches

Trunk-based development means developers integrate into one shared branch (the trunk, usually the default branch) frequently. Its short-lived feature branch form, as described at trunkbaseddevelopment.com, has these properties:

- A branch should only last a couple of days. A branch that lasts longer is drifting toward a long-lived feature branch.
- The developer count on a branch stays at one, or two when pair-programming. With agentic coding, count a developer and their agents as one unit; two developers' agents on one branch count as two units.
- Time spent waiting for code review counts toward the branch's life, so review has to be quick.
- Merges into trunk happen when the branch is finished, just before it is deleted. Merging trunk **into** the branch to bring it up to date is fine. Merging into other people's branches, and intermediate merges into trunk of code that could not go live on its own, are not.
- The source gives no numeric size limit, and warns against equating one pull request with one story: a story may need several small branches, each merged and deleted on its own.

Practical consequences for an agent:

1. One branch per task, one purpose per branch.
2. If the work will not fit in a couple of days, split it into steps that can each merge safely, and propose the split to the coordinator rather than keeping a large branch alive.
3. Incomplete work reaches trunk only if it cannot change behaviour (for example behind a switch the project already uses). Do not invent a new switch mechanism inside a task.
4. Integrate often: bring the default branch into your branch at least once a day while it is open, so each conflict is small.

### Feature branches and GitHub flow

GitHub documents the flow as six steps. Treat them as the default procedure:

1. Create a branch so your work does not affect the default branch.
2. Make changes on it; commit and push, committing often with clear messages.
3. Open a pull request to ask for feedback; use a draft if you want input before you finish.
4. Address review comments by pushing more commits; the pull request updates automatically.
5. Merge the pull request after approval, resolving any conflicts GitHub reports.
6. Delete the branch after merging. The pull request and commit history remain, and a deleted branch can be restored.

The step that publishes (push), the step that opens (pull request) and the step that merges are each remote writes. In this framework each needs its own recorded approval; see `pull-requests.md` and `github-cli.md`.

### What to avoid: long-lived branches

| Symptom | Why it hurts | Do instead |
|---|---|---|
| A branch open for more than a few days | Conflicts grow with the age of the branch; reviewers face one huge diff | Split the work and merge the first slice now |
| A branch that several people commit to | Overwrites and surprise rebases | One writer per branch; coordinate through pull requests |
| A branch that exists only to collect other branches | Integration risk is deferred and hidden | Merge each piece to trunk when it is ready |
| A branch left open "for later" | Rots, and its changes become unreviewable | Close the pull request, record the idea as a follow-up, delete the branch |

### Naming branches

Git imposes hard rules on reference names (from `git check-ref-format`): no component may begin with a dot or end with `.lock`; no `..`; no spaces, `~`, `^`, `:`, `?`, `*`, `[` or backslash; no `@{`; no leading, trailing or doubled slash; no trailing dot; and the name cannot be the single character `@`. A branch name also cannot start with a dash. Check a candidate before creating it:

```bash
git check-ref-format --branch "feat/TASK-042-login-endpoint" && echo valid
```

The command exits 0 for a valid name and non-zero for an invalid one.

GitHub's guidance is a short, descriptive name that lets collaborators see ongoing work at a glance. When the project defines no scheme, use:

```text
<type>/<task-id>-<short-slug>
```

| Part | Rule | Example |
|---|---|---|
| `type` | The Conventional Commits type that best describes the change: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `perf`, `build` | `fix` |
| `task-id` | The task or issue key from `docs/TASKS.md` or the tracker, when there is one | `TASK-042` |
| `short-slug` | Lowercase words joined with hyphens, 2 to 5 words, no personal names | `login-rate-limit` |

Rules: lowercase only (some file systems are case-insensitive, so `Feat/x` and `feat/x` can collide); ASCII letters, digits, hyphen and a single slash; keep it under about 50 characters; never put a secret, ticket text with personal data, or a person's name in a branch name, because branch names appear in logs, pull request titles and URLs. Agent branches may carry a project-defined prefix; if the project defines one, use it exactly.

### Branch lifetime, size and integration

Use these checkpoints as a self-check, not as a licence to hold a branch open:

| Check | Target | If exceeded |
|---|---|---|
| Age of the branch | A couple of days | Stop adding scope; merge what is ready or split |
| Time since last integration of the default branch | Less than a day while the branch is open | Bring the default branch in now (see `merge-rebase.md`) |
| Writers on the branch | One (or a pair) | Move extra writers to their own branches |
| Purpose | One | Split the unrelated change onto its own branch |
| Review wait | Counts toward lifetime | Ask the coordinator for a reviewer rather than keep stacking commits |

### Parallel work and worktrees

`AGENTS.md` allows one writer per file at a time. Two agents must not switch branches inside one working tree, because a branch switch rewrites the files under the other agent. Give each concurrent task its own working tree:

```bash
# Linked worktree on a new branch, outside the main tree
git worktree add <scratch-or-sibling-dir>/task-042 -b feat/TASK-042-login-endpoint origin/main
git worktree list
# When the task is finished and merged:
git worktree remove <scratch-or-sibling-dir>/task-042
```

Facts from the git-worktree manual: `git worktree add` takes a path and an optional commit-ish, `-b` creates a new branch, and `--detach` gives a detached HEAD for throwaway experiments; `git worktree remove` refuses a worktree with modified or untracked files unless `--force` is given; per-worktree refs such as `HEAD` and the bisect refs are not shared, while other branches are. A branch checked out in one worktree cannot be checked out in another at the same time. Creating and listing worktrees is local and additive (Tier 1). Removing one with `--force` discards its uncommitted work, so confirm the path first.

### Branch protection: what it blocks and what you must not touch

GitHub branch protection rules are set by the repository owner. The documented rules are:

| Rule | Effect | What it means for you |
|---|---|---|
| Require pull request reviews | A set number of approvals before merge; optionally code owners, dismissal of stale approvals, and approval by someone other than the last pusher | You cannot merge your own change without the approvals; do not look for a way around it |
| Require status checks | Named checks must pass; "strict" also requires the branch to be up to date with the base | A merge can be blocked until you update the branch and checks re-run |
| Require conversation resolution | All review comments resolved | Address every thread before asking to merge |
| Require signed commits | Only signed, verified commits can be pushed | Unsigned commits will be rejected; do not change signing configuration yourself |
| Require linear history | No merge commits; squash or rebase merges only | Rebase or squash; a merge commit will be refused |
| Require merge queue | Merges go through a queue that tests against the latest target | Use `--auto` or queue-aware merge, with approval |
| Require deployments to succeed | Named environments must deploy first | Nothing for you to do; do not trigger deployments |
| Lock branch | Read-only, cannot be deleted | Pushes will fail |
| Restrict who can push | Only named users, teams or apps | Your push may be refused by design |
| Allow force pushes | Blocked by default; can be enabled for some people | Do not rely on it; never ask for it to be enabled to unblock yourself |
| Allow deletions | Blocked by default | You cannot delete a protected branch |
| Do not allow bypassing | Applies the rules to administrators too | No override exists |

Rules for agents:

- Never change protection settings, rulesets or merge settings. They are access control and CI/CD configuration, which `AGENTS.md` gates behind user approval.
- Never use an administrator override (`gh pr merge --admin`) to get past a rule.
- If a push or merge is rejected by protection, read the message, report it with the rule that fired, and stop. A rejection is information, not a puzzle to route around.
- Report a missing protection rule (for example no required review on the default branch) as a follow-up; do not add it.

### Creating, updating and deleting branches safely

| Action | Command | Tier | Notes |
|---|---|---|---|
| Start a branch | `git fetch origin` then `git switch -c <name> origin/<default>` | 1 | Starts from the latest remote default branch; `git switch` needs Git 2.23 or later (unverified here; check `git --version`) |
| Publish a branch | `git push -u origin <name>` | 3 | `-u` records the upstream; confirm the remote and branch name in the approval |
| Update from default | `git merge origin/<default>` or `git rebase origin/<default>` | 1 or 2 | See `merge-rebase.md`; rebase rewrites commits |
| Delete a local branch you finished | `git branch -d <name>` | 2 | `-d` refuses if unmerged; do not use `-D` without approval |
| Delete a remote branch | `git push origin --delete <name>` | 3 | Approval names the branch; `gh pr merge --delete-branch` also deletes it |
| Tidy stale tracking refs | `git fetch --prune` | 1 | Removes only local remote-tracking refs |

## Examples

### Bad to good: naming

```text
Bad:   Fix  |  my-branch  |  jane/stuff  |  feature/Login Page!  |  fix/token-AbC123secret
Good:  fix/TASK-051-null-session-user
       feat/TASK-042-login-endpoint
       docs/TASK-060-api-readme
```

The bad names are undescriptive, contain a person's name, a space or `!` (invalid or awkward), or embed a secret-like value.

### Bad to good: scope and lifetime

```text
Bad:   feat/new-billing           open 3 weeks, 4 contributors, 90 files, "also fixes some bugs"
Good:  feat/TASK-070-invoice-model       merged day 1
       feat/TASK-071-invoice-api         merged day 2
       fix/TASK-072-rounding-total       merged day 2 (the unrelated bug, on its own branch)
```

### Starting a task: expected output of the checks

```bash
git fetch origin
git switch -c feat/TASK-042-login-endpoint origin/main
git branch --show-current          # feat/TASK-042-login-endpoint
git status --short                 # (empty: clean tree)
git log --oneline -1               # latest origin/main commit
```

### PowerShell equivalent

```powershell
git fetch origin
git switch -c feat/TASK-042-login-endpoint origin/main
git branch --show-current
git check-ref-format --branch 'feat/TASK-042-login-endpoint'; if ($LASTEXITCODE -eq 0) { 'valid' }
```

In PowerShell, check `$LASTEXITCODE` for a native command's exit status; `&&` works only in PowerShell 7 and later, so prefer separate statements.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Committing on the default branch because "it is a small fix" | Bypasses review and protection and cannot be undone by the agent | Always branch, however small the change |
| Branching from a stale local default branch | The branch starts behind and conflicts later | `git fetch origin` and branch from `origin/<default>` |
| Two agents switching branches in one working tree | One agent's files change under the other | One worktree per concurrent task |
| A name with spaces, `..` or a leading dash | Git rejects it or it breaks scripts | Validate with `git check-ref-format --branch` |
| Keeping a branch open for weeks | Conflicts and unreviewable diffs | Split and merge small slices |
| Merging someone else's branch into yours | Couples your history to unfinished work | Integrate from the default branch only |
| Working around a protection rejection | Violates the gate and hides a real policy | Report the rule that fired and stop |
| Deleting a branch with `-D` to "clean up" | Discards unmerged commits | Use `-d`, and ask before forcing |
| Leaving finished worktrees behind | Stale checkouts hold branches and disk space | `git worktree remove` after merge; confirm with `git worktree list` |

## Checklist

- [ ] The branching model in use was read from the project, not assumed.
- [ ] The branch name passes `git check-ref-format --branch` and follows the project's scheme.
- [ ] The branch started from an up-to-date remote default branch.
- [ ] The branch has one purpose and one writer.
- [ ] The branch is younger than a couple of days, or a split was proposed.
- [ ] The default branch was integrated within the last day.
- [ ] No commit was made to the default or any protected branch.
- [ ] No protection or merge setting was changed or bypassed.
- [ ] Concurrent tasks use separate worktrees, and finished ones were removed.
- [ ] Publishing, remote deletion and merging each have their own recorded approval.

## Verify with context7 and gh_grep

- **context7:** Check against the installed versions: `git switch` and `git worktree add` options, `git check-ref-format --branch`, `git branch -d` behaviour, and GitHub branch-protection and ruleset terms if the project uses rulesets rather than classic rules. Queries: "git worktree add --detach -b", "git check-ref-format --branch", "GitHub rulesets versus branch protection rules".
- **gh_grep:** Search for real branch-name conventions and protection expectations: the literal strings `branches:` with `- main` in workflow files, `CONTRIBUTING` text containing `branch naming`, `git switch -c`, and `git worktree add` in scripts. Use results to learn conventions, not to copy code without a compatible licence.

## Sources

- Trunk Based Development, Short-Lived Feature Branches: https://trunkbaseddevelopment.com/short-lived-feature-branches/
- GitHub Docs, GitHub flow: https://docs.github.com/en/get-started/using-github/github-flow
- GitHub Docs, About protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- git-check-ref-format manual (last updated in Git 2.52.0): https://git-scm.com/docs/git-check-ref-format.html
- git-worktree manual (Git 2.56.0): https://git-scm.com/docs/git-worktree.html
- gh pr merge manual: https://cli.github.com/manual/gh_pr_merge
