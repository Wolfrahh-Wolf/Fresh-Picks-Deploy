# Merge, Rebase and Recovery

How to choose between merge and rebase, resolve conflicts, recover from mistakes, and apply the force-push rules; assumes Git 2.x (merge manual at 2.56.0, rebase manual at 2.54.0, push manual at 2.55.0, reflog manual at 2.51.1), checked 2026-11-27. Anything that rewrites history or writes to a remote needs recorded approval under `AGENTS.md`.

## Contents

- The decision: merge, rebase or neither
- Safety tiers for integration commands
- Updating a feature branch
- Resolving conflicts
- Rebase mechanics you will need
- Backing up before any rewrite
- Safe recovery
- Force-push rules
- Undoing published work: revert

## Guidance

### The decision: merge, rebase or neither

| Situation | Choose | Why |
|---|---|---|
| Bring the latest default branch into your own unpublished branch | Rebase onto it, with approval, or merge it in | Rebase gives linear history; merge keeps your commits untouched and needs no rewrite |
| Bring the default branch into a branch already pushed or under review | Merge it in | A rebase would rewrite published commits and need a force push |
| Others have based work on your branch | Merge only | The rebase manual warns that rewriting a branch others have based work on forces them to repair their history by hand |
| Finish a pull request | Use the merge method the project chose (see `pull-requests.md`) | The host performs it; you do not hand-merge into the default branch |
| Undo a commit that is already on a shared branch | `git revert` | Adds a new commit; rewrites nothing |
| Tidy your own unpublished commits | Interactive rebase with `fixup` or `reword`, with approval | Local rewrite, safe only if nobody has the commits |
| Move a branch to a different base | `git rebase --onto`, with approval | Precise, but rewrites every moved commit |

Rule of thumb: **rebase what is private, merge what is shared, revert what is published.** A commit is published once it has been pushed anywhere another person or tool can fetch it, including a pull request branch.

Merge and rebase produce the same final tree for the same conflicts. They differ in history: a merge preserves the real order of work and adds a merge commit; a rebase replays your commits on a new base, giving them new hashes. Use the project's stated preference. If a protected branch requires linear history, merge commits are refused there.

### Safety tiers for integration commands

| Command | Tier | Note |
|---|---|---|
| `git fetch`, `git log origin/<default>..HEAD`, `git diff origin/<default>...HEAD` | 0 and 1 | Read and download only |
| `git merge origin/<default>` into your own feature branch | 1 | Local and additive; creates a merge commit; abortable |
| `git merge --no-commit --no-ff <ref>` | 1 | Previews a merge without committing |
| `git rebase`, `git rebase -i`, `git commit --amend`, `git reset --hard`, `git cherry-pick` onto an existing branch | 2 | Rewrites or discards local state; needs approval and a backup |
| `git push` of any kind | 3 | Remote write |
| Merging into the default or a protected branch | 3 | Done through a pull request, with approval |
| `git merge --abort`, `git rebase --abort`, `git rebase --quit` | 1 | Returns toward the pre-operation state; see caveats below |

Debugger: none of the rewrite or remote commands apply. Use read-only history commands and a disposable worktree.

### Updating a feature branch

Before you start, confirm the tree is clean and know where you are:

```bash
git status --short                 # must be empty, or you know exactly why not
git branch --show-current
git fetch origin
git log --oneline HEAD..origin/<default>    # what you are about to integrate
git branch backup/<branch>-before-update    # cheap safety net (Tier 1)
```

**Merge route (no rewrite):**

```bash
git merge origin/<default>          # fast-forwards if possible, otherwise creates a merge commit
```

Options: `--ff` is the default; `--no-ff` always creates a merge commit; `--ff-only` fast-forwards or refuses with a non-zero status, which makes it a safe probe. `--no-commit` stops before the merge commit so you can inspect it (combine with `--no-ff`, because a fast-forward cannot be stopped). `--squash` stages the combined changes without committing and without recording the merge, which is not a way to update a branch.

**Rebase route (rewrites; approval first):**

```bash
git rebase origin/<default>
```

Replays your commits on top of the new tip. Without `--onto`, the new base is the upstream argument; with `--onto <newbase> <oldbase> <branch>`, you choose both ends:

```bash
git rebase --onto origin/<default> <old-parent-branch> <branch>   # move a branch off a parent that merged elsewhere
```

By default the rebase linearises history and drops merge commits. `--rebase-merges` recreates the topology instead; resolved conflicts inside merges must be redone by hand. `--update-refs` also moves other branches that point at commits being rebased (not branches checked out in another worktree). `--keep-base` keeps the merge base as the starting point.

After a rebase, the branch has new commit hashes; if it was ever pushed, the next push is a force push (see below) and needs its own approval.

### Resolving conflicts

A conflict is a request for a decision, not an error. Work in this order.

1. **Stop and look.** `git status` lists the conflicted paths ("both modified"). Do not start editing blindly.
2. **Understand both sides.** For each conflicted path:
   - `git diff` shows the three-way view of what is still in conflict.
   - `git log --merge -p <path>` shows the commits from each side that touch the path.
   - `git show :1:<path>`, `:2:<path>` and `:3:<path>` show the common ancestor, your side (HEAD) and the other side (MERGE_HEAD).
   - `git ls-files -u` lists the conflicted index entries.
3. **Add context to the markers.** The default markers show your side (`<<<<<<<` to `=======`) and theirs (`=======` to `>>>>>>>`). Setting `merge.conflictStyle` to `diff3` adds the common ancestor between `|||||||` and `=======`; `zdiff3` does the same but trims matching lines at the edges. Showing the ancestor makes it clear what each side changed. Changing configuration is local to the repository only if you use `git config` without `--global`; leave user-level configuration alone.
4. **Decide, do not pick a side.** The correct result is usually a combination. Ask what each side was trying to achieve and keep both intents. If you cannot tell, stop and escalate.
5. **Edit the file** to the intended final content and remove every marker. Search the file for `<<<<<<<`, `=======` and `>>>>>>>` before staging.
6. **Mark resolved:** `git add <path>`, one file at a time.
7. **Verify before concluding.** Run the build, type-check, lint and tests. A textual merge can be semantically broken (a renamed function still called by the old name) with no conflict marker at all.
8. **Conclude:** `git merge --continue` or `git rebase --continue`. For a rebase, repeat from step 1 for each commit that conflicts; `git rebase --skip` drops the current patch and is almost never what you want.
9. **Re-check the result:** `git diff origin/<default>...HEAD --stat` should show only your intended changes, and `git status` should be clean.

Rules:

- **Never blanket-resolve with `-X ours`, `-X theirs`, or `checkout --ours/--theirs` on a whole file.** `-X ours` resolves only the conflicting hunks in your favour while still taking non-conflicting changes from the other side; it silently discards the other side's intent in those hunks. It is not the same as the merge strategy `-s ours`, which discards everything the other branch changed.
- **Generated and lock files** (dependency lockfiles, compiled output, snapshots): do not hand-merge. Take the default branch's version, then regenerate with the project's tool, and commit the result. Adding or majorly upgrading a dependency still needs approval.
- **Conflicts in tests**: never delete or weaken a test to make a conflict disappear.
- **Conflicts in migrations or schema**: never edit an applied migration; stop and escalate, because the order of migrations is a design decision.
- **Conflicts in security-sensitive code** (authentication, authorization, cryptography, secrets handling): finish the resolution, then flag the file to the coordinator, because the change is high-risk under `AGENTS.md`.
- **If the resolution is a guess, say so.** Report each conflicted file, how you resolved it and what verification you ran.
- **Abort when lost.** `git merge --abort` and `git rebase --abort` cancel the operation and try to restore the pre-operation state. They may not recover uncommitted changes that existed before the operation began, which is why you start from a clean tree.

### Rebase mechanics you will need

Interactive rebase (`git rebase -i <base>`) edits the todo list. The documented commands:

| Command | Effect |
|---|---|
| `pick` | Keep the commit |
| `reword` | Keep it, edit the message |
| `edit` | Stop after applying so you can amend or add commits |
| `squash` | Meld into the previous commit and combine messages |
| `fixup` | Like `squash`, discarding this commit's message |
| `drop` | Remove the commit |
| `exec <cmd>` | Run a command; the rebase stops if it fails |
| `break` | Stop here |

Prepare fixes for later squashing with `git commit --fixup=<commit>`, then run `git rebase -i --autosquash <base>`; commits whose subject begins `fixup!`, `squash!` or `amend!` are moved after their target automatically. Interactive rebase opens an editor, which an agent cannot use; the non-interactive route is to ask the user to run it, or to set an editor environment variable for one command, which is a configuration decision to raise with the coordinator.

Mode options (each stands alone): `--continue` resumes after a resolved conflict; `--skip` skips the current patch; `--abort` returns to the original branch state; `--quit` stops but leaves HEAD, index and working tree as they are; `--edit-todo` edits the list; `--show-current-patch` shows the patch being applied.

### Backing up before any rewrite

Before every Tier 2 command that rewrites commits:

```bash
git status --short                              # clean, or understood
git branch backup/<branch>-<yyyymmdd>-<what>    # a ref at the current tip (Tier 1)
git rev-parse HEAD                              # record the SHA in the report
```

A branch keeps the old commits reachable for as long as it exists, with no dependence on reflog expiry. Remove your backup branch only after the work is merged and the user no longer needs it (branch deletion is a Tier 2 action). Never push a backup branch unless asked.

### Safe recovery

Git rarely loses committed work in the short term. Recover in this order, least destructive first.

| Situation | Recover with | Tier |
|---|---|---|
| A merge or rebase is in progress and going wrong | `git merge --abort` or `git rebase --abort` | 1 |
| A rebase finished and the result is wrong | `git reflog`, find the pre-rebase entry, then `git switch -c recovery/<name> <sha>` to rescue it as a new branch; only then decide about resetting | 1 |
| You want the branch itself back at the old tip | `git reset --hard <sha>` after the rescue branch exists | 2 (discards uncommitted work) |
| A commit "disappeared" after a reset or amend | `git reflog` then `git branch recovery/<name> <sha>` | 1 |
| A branch was deleted locally | `git reflog` to find its last tip, then `git branch <name> <sha>` | 1 |
| A bad commit is already pushed | `git revert`, never a rewrite | 3 |
| Uncommitted work was overwritten | Possibly unrecoverable; stop and report | n/a |

Facts about the reflog (git-reflog manual): it records when the tips of branches and other references were updated in the **local** repository, so it exists only on the machine where the work happened and is not pushed; `git reflog show` (the default) shows `HEAD`, `branch@{n}` names where a branch pointed n moves ago, and `HEAD@{2}` means where HEAD was two moves ago; entries are pruned by age, with `gc.reflogExpire` defaulting to 90 days and `gc.reflogExpireUnreachable` to 30 days for entries no longer reachable from the tip. Do not run `git reflog expire` or `git gc --prune` while recovering.

`ORIG_HEAD` points at the old tip at the start of a rebase, but other commands (such as `git reset`) can change it during the operation, so the rebase manual calls the branch reflog the reliable source: the previous tip is at `@{1}`.

In PowerShell, quote reflog selectors, because `@{` begins a hashtable literal:

```powershell
git reset --hard 'ORIG_HEAD'      # only if you are sure it is still the old tip
git switch -c recovery/login '@{1}'
git log -g --oneline -10
```

### Force-push rules

A force push replaces a remote branch with your local one and can delete other people's commits. It is both a history rewrite and a remote write, so it needs approval, and the approval must name the **exact branch** and the **expected remote SHA**.

| Rule | Detail |
|---|---|
| Never `git push --force` or `-f` | It disables the safety checks and "can cause the remote repository to lose commits". It also applies to every ref being pushed; with `push.default=matching` or several destinations it can overwrite refs other than the current branch |
| Never force-push the default branch, a release branch, or any protected branch | Protection blocks force pushes by default; do not ask for that to be changed |
| Only your own, unmerged feature branch | One writer per branch |
| Use `--force-with-lease` | The push fails if the remote ref no longer holds the value you expect, so you cannot silently erase a teammate's new commit |
| Add `--force-if-includes` | It forces the update only if the remote-tracking tip is reachable from your local branch's reflog, i.e. you integrated what you fetched, including a background fetch. It only works together with `--force-with-lease` in its bare or `=<refname>` form |
| Prefer the explicit lease for certainty | `--force-with-lease=<ref>:<expected-sha>` pins the exact value you were approved to replace. The manual notes the other forms are still experimental, and that any background `git fetch` (an editor, a scheduled job) updates the remote-tracking ref and can defeat the implicit lease |
| Name one ref | `git push origin <branch>`, never a bare `git push` that might push several refs; a `+` before one refspec forces only that ref |
| Dry run first | `git push --dry-run` does everything except send the update; use it to confirm the refs |
| Tell people afterwards | Anyone who pulled the old commits must reset their branch to the new one |

The sequence an approved force push follows:

```bash
git fetch origin                                              # refresh the tracking ref you will lease against
git rev-parse origin/<branch>                                 # record the expected remote SHA: <expected>
git branch backup/<branch>-before-force                      # local safety net
git push --dry-run --force-with-lease=<branch>:<expected> origin <branch>
# after approval that names <branch> and <expected>:
git push --force-with-lease=<branch>:<expected> origin <branch>
git ls-remote --heads origin <branch>                         # confirm the new SHA
```

Use the explicit form whenever you can name the expected SHA. When you cannot, the fallback is the bare pair `git push --force-with-lease --force-if-includes origin <branch>`; the manual says `--force-if-includes` has no effect with the `=<refname>:<expect>` form, so do not combine them.

If the push is rejected with a stale-info error, someone else updated the branch. Do not retry with a stronger force: fetch, inspect `git log HEAD..origin/<branch>`, and report.

### Undoing published work: revert

`git revert <commit>` records a new commit that applies the opposite change. It needs a clean working tree.

- A merge commit needs `-m <parent-number>` (parent numbering starts at 1; `-m 1` keeps the first parent, normally the branch merged into, as the mainline), because Git cannot know which side is the mainline.
- `--no-commit` (`-n`) applies the change without committing, to revert several commits as one; `--no-edit` skips the message editor.
- **Reverting a merge declares that you never want the tree changes the merge brought in.** Later merges of that branch will bring only commits that were not ancestors of the reverted merge, so re-merging the same branch later does not restore the reverted changes. This may or may not be what you want; the git-revert manual links to a how-to ("revert a faulty merge") for the follow-up procedure. Report this consequence before reverting a merge.
- Explain **why** in the message, and use the `revert:` type from `conventional-commits.md`.
- Pushing the revert is a Tier 3 action.

## Examples

### Bad to good: updating a pushed branch

```text
Bad:   git pull --rebase; git push --force
       (rewrites a published branch with no approval, no lease, no backup)

Good:  git fetch origin
       git merge origin/main                 # branch is under review, so merge, no rewrite
       <run tests, lint, build>
       -> ask: push feat/TASK-042-login to origin (fast-forward, 2 commits ahead)
```

### Conflict resolution record

```text
Operation: git merge origin/main into feat/TASK-042-login-endpoint
Conflicts: src/routes/index.ts (both modified), package-lock.json (both modified)
src/routes/index.ts: main added the /health route; this branch added /api/auth.
  Resolution: kept both route registrations, in alphabetical order. Verified: npm test, 142/142.
package-lock.json: took origin/main's version, then ran the project's install command to
  regenerate it. No dependency was added or upgraded.
Result: 1 merge commit 7b21e4d. Backup: backup/feat-TASK-042-before-update at 3f9a1c0.
```

### Recovering from a bad rebase

```bash
git rebase origin/main            # went wrong, and it has finished
git reflog -10                    # find "rebase (start)" and the entry just before it: abc1234
git switch -c recovery/login abc1234   # rescue the old tip on its own branch
git diff recovery/login HEAD --stat    # compare before deciding anything else
```

### Force push request wording

```text
Action:   force-push feat/TASK-042-login-endpoint to origin using --force-with-lease
Target:   origin, branch feat/TASK-042-login-endpoint only; expected remote SHA 3f9a1c0
Why:      rebased onto origin/main to satisfy required linear history
Risk:     replaces 3 remote commits; anyone who pulled them must reset
Rollback: backup/feat-TASK-042-before-force at 3f9a1c0; git push --force-with-lease=<branch>:<new-sha> restores it
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `git push --force` | Can overwrite others' commits and every ref pushed | `--force-with-lease` with an explicit expected SHA, after approval |
| Rebasing a pushed or shared branch | Forces everyone downstream to repair history | Merge the default branch in; rebase only private branches |
| Starting a merge or rebase with a dirty tree | Abort may not restore the uncommitted changes | Commit or park changes first (with approval for stash drops) |
| Resolving with `-X ours` or `-X theirs` everywhere | Silently discards one side's intent | Resolve each hunk by understanding both sides |
| Not testing after a conflict resolution | A clean merge can still break behaviour | Build, type-check, lint and test before `--continue` |
| `git reset --hard` as the first recovery step | Discards the evidence | Rescue the old tip on a branch from the reflog first |
| Trusting `ORIG_HEAD` after a rebase | Other commands may overwrite it | Use the branch reflog (`@{1}`) |
| Reverting a merge without `-m` | Git refuses, or you revert the wrong side | `git revert -m 1 <merge>` and note the re-merge consequence |
| Retrying a rejected force push with a stronger flag | Overwrites the new commit the lease was protecting | Fetch, inspect, report |
| Unquoted `@{1}` in PowerShell | Parsed as a hashtable literal | Quote it: `'@{1}'` |
| Hand-merging a lockfile | Produces an inconsistent dependency tree | Take one side and regenerate |

## Checklist

- [ ] The choice of merge, rebase or revert follows the private, shared, published rule.
- [ ] The working tree was clean and a backup branch recorded before any rewrite.
- [ ] No Tier 2 or Tier 3 command ran without recorded approval for that exact action.
- [ ] Each conflicted file was resolved by understanding both sides, with no blanket `-X ours` or `-X theirs`.
- [ ] No conflict marker remains (`git grep -n -e '<<<<<<<' -e '>>>>>>>'` returns nothing).
- [ ] Build, type-check, lint and tests passed after resolution.
- [ ] `git diff origin/<default>...HEAD --stat` shows only the intended changes.
- [ ] Any force push used `--force-with-lease`, named one branch, and recorded the expected SHA.
- [ ] No force push touched the default or a protected branch.
- [ ] The old tip is still reachable (backup branch and reflog) after a rewrite.
- [ ] A merge revert, if any, stated the re-merge consequence.

## Verify with context7 and gh_grep

- **context7:** Confirm at the installed Git version: `git push --force-with-lease` forms and `--force-if-includes`; `git rebase --update-refs`, `--autosquash`, `--onto`, `--rebase-merges`; `git merge --no-commit --no-ff` and `--ff-only`; `merge.conflictStyle` values `diff3` and `zdiff3`; `git revert -m`; reflog expiry defaults. Queries: "git push force-with-lease force-if-includes", "git rebase update-refs", "git merge conflictStyle zdiff3", "git revert mainline".
- **gh_grep:** Search for real usage: `--force-with-lease`, `--force-if-includes`, `rebase --onto`, `git revert -m 1`, `merge.conflictStyle` and `zdiff3` in scripts, CONTRIBUTING files and CI configuration. Look at how mature projects document the force-push rule; do not copy scripts without a compatible licence.

## Sources

- git-merge manual (Git 2.56.0): https://man.archlinux.org/man/git-merge.1.txt
- git-rebase manual (last updated in Git 2.54.0): https://git-scm.com/docs/git-rebase.html
- git-push manual (Git 2.55.0): https://git-scm.com/docs/git-push.html
- git-reflog manual (last updated in Git 2.51.1): https://git-scm.com/docs/git-reflog.html
- git-revert manual (last updated in Git 2.54.0): https://git-scm.com/docs/git-revert.html
- GitHub Docs, About protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Microsoft Learn, about_Quoting_Rules (PowerShell 7.6 documentation): https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_quoting_rules
