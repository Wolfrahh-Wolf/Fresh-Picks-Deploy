# README

How to structure `README.md`, write a quick start that works, and prove every documented command; assumes GitHub-flavoured Markdown rendering, the RelayCrew README template and the GitHub README documentation, checked 2026-11-26. The project's own manifest, `AGENTS.md` and existing README conventions win over these defaults.

## Contents

- Role and purpose of the README
- Structure and section rules
- Quick start design
- Requirements, configuration and secrets
- Links and the documentation index
- Verifying every command
- Keeping the README short and current

## Guidance

### Role and purpose of the README

The implementer owns `README.md`. It is the entry point for a person who has just cloned the repository. GitHub's own guidance says a README tells people why the project is useful, how to get started, where to get help, and who maintains and contributes. Everything longer belongs in `docs/` and is linked.

Classify each part by Diátaxis type, so the page does not blur them (the full rules are in [api-documentation.md](api-documentation.md)):

| README part | Type | Rule |
|---|---|---|
| Purpose sentence, short overview | Explanation, kept to one or two sentences | Link to `docs/ARCHITECTURE.md` for more |
| Setup and quick start | Tutorial-like: the reader does steps and sees results | One path, no options, a visible result per step |
| Usage snippets | How-to | One goal per snippet, for a competent reader |
| Configuration table | Reference | Facts only, no instructions |

Decide where each fact lives before you write it. A fact that already has a home is linked, not copied: environment variable names live in `.env.example`, endpoints in `docs/API-CONTRACTS.md`, the schema in `docs/DB.md`.

### Structure and section rules

Keep the template's headings and order: title, purpose sentence, `Requirements`, `Setup`, `Usage`, `Testing`, `Configuration`, `Documentation`. Add a section only when the project needs it and the template has no home for it, for example `License` or `Contributing`. Add them only when the file or process exists. Choosing a licence is a decision for the user. Never pick one.

| Section | Contains | Does not contain |
|---|---|---|
| Title and purpose | Project name, one sentence on what it does and for whom | Slogans, feature lists, badges that show no real status |
| Requirements | Runtime and tool versions the project needs, taken from the manifest or version files | Versions copied from memory |
| Setup | Ordered commands from clone to a runnable project | Alternatives, platform essays, troubleshooting prose |
| Usage | The smallest working example per main task, with the expected output | Full option listings (link to reference) |
| Testing | The exact test, lint and build commands from the `Commands` line of `AGENTS.md` | Test strategy |
| Configuration | Table of variable names, meaning, default or `required`, pointing at `.env.example` | Values, secrets, hostnames |
| Documentation | Links to the files in `docs/` that exist | Links to files that do not exist |

If the README commands and the `Commands` line in `AGENTS.md` disagree, the manifest's real scripts decide which is correct. Report the mismatch. Do not edit `AGENTS.md` yourself.

Where GitHub looks for a README: `.github`, then the repository root, then `docs`, in that precedence. Edit the one that exists. Never create a second README that is hidden by a higher-precedence one.

### Quick start design

A quick start is a tutorial in miniature. Apply these rules:

1. Open with prerequisites in one line, linking to `Requirements`.
2. Number the steps. Each step is one action, in one code block, in the order a new person must perform them.
3. After each step that has an observable result, say what the reader should see: a printed line, a port, a page, an exit status.
4. Keep explanation to the minimum the action needs. Link out for the rest.
5. Offer one path. Alternatives go to a how-to guide.
6. Aim for a working result in about five steps. If it needs more, the project's setup is the problem: report it as a follow-up rather than padding the README.
7. End with the next step: a link to `Usage` or a guide.

Warn before any step that changes state outside the working directory, such as deleting data, resetting a database, or sending data to a remote service. Write the warning above the command, name the effect, and say the step needs the reader's deliberate choice. Never put a destructive command in a quick start unless the project cannot start without it.

### Requirements, configuration and secrets

- Read versions from the project's own files: the package manifest's engine fields, a version file, the container base image, the CI matrix. Quote the minimum supported version, not the newest you happen to have installed.
- When a version appears in several places, state it once in the README and make the others agree. If they disagree, report the mismatch.
- Configuration lists names only. For each name give the meaning and whether it is required. Real values, secrets and internal hostnames never appear. Use placeholders such as `<DATABASE_URL>`, `<API_TOKEN>`.
- When a change adds a variable, the same change adds it to `.env.example` and to the README table. Search the code for every environment variable it reads and confirm each appears in both.
- If the project supports Windows (`AGENTS.md` refers to PowerShell), give the Windows command beside the POSIX command in setup steps. If it does not, say which platforms are supported.

### Links and the documentation index

- Use relative links inside the repository. GitHub resolves them against the branch being viewed, and they keep working in clones. Absolute links to the repository's own branch do not.
- Keep link text on one line. A line break inside link text breaks the link on GitHub.
- The `Documentation` list names each doc that exists. If a template link points at a file the project does not have yet, do not leave it dangling. Remove it or ask the architect to create the file, and say which in `Docs impact`.
- GitHub truncates a README rendered beyond 500 KiB and builds a table of contents from headings, so clear, unique headings matter more than a hand-made contents list.

### Verifying every command

Every command in the README must be proven, not assumed. Procedure:

1. **Inventory.** List each command in fenced blocks and inline code, including those inside prose steps.
2. **Classify.** Mark each command as *safe-local* (builds, tests, starts a local server, prints help), *destructive* (deletes files or data, resets or migrates a database, rewrites history), *remote-writing* (deploys, publishes, pushes, calls a paid or production service) or *needs secrets*.
3. **Run safe-local commands in a clean state.** Use a fresh clone or an empty working directory, with only the documented prerequisites installed and no cached build output or leftover environment. A command that only works because of local residue is a defect in the README.
4. **Record** the command, its exit status and the line of output the README promises.
5. **Do not run destructive, remote-writing or secret-dependent commands** unless the brief records the user's approval for that exact action and a local or test target. Verify them another way: run with a help or dry-run flag if the tool has one, confirm the script exists in the manifest, read the script, and compare the flags with the tool's documentation through context7. Label the result `not run: <reason>`.
6. **Check outputs.** If the README shows expected output, compare it with the real output and fix the README, not the program.
7. **Check names.** Confirm that every script, target and file the commands mention exists: search the manifest's script names, task runner targets and paths.

Never paste a real token, password or private URL into a command to make it run. Use `.env.example` copied to the local, untracked environment file, with test values.

### Keeping the README short and current

- A README that needs more than about one screen of reference or explanation has the wrong content. Move the detail to `docs/` and link it.
- State the facts that change least. Link for the rest.
- On every sync, check the README against these triggers: setup steps changed, a command or flag was added or renamed, a variable was added, a port or default changed, a public interface changed, a documented doc file was added or removed, the supported runtime changed.
- Docs describe what is true now. Do not leave roadmap promises in the README.

## Examples

### Bad to good: quick start

Bad:

~~~~markdown
## Setup

Install the dependencies and configure the environment, then start the app.
You may need a database. Check the docs.
~~~~

Good:

~~~~markdown
## Setup

Requires Node.js 22 or later and PostgreSQL 16 (see Requirements).

1. Install dependencies:

   ```bash
   npm ci
   ```

2. Create your local environment file and set `DATABASE_URL`:

   ```bash
   cp .env.example .env
   ```

3. Apply the schema to your **local** database. This changes the database that `DATABASE_URL` points at, so do not run it against a shared environment:

   ```bash
   npm run db:migrate
   ```

4. Start the server. You should see `Listening on http://localhost:3000`:

   ```bash
   npm run dev
   ```
~~~~

Each step is one action, the destructive step is flagged, and the expected output is stated. The commands above are illustrative: the real ones come from the project's manifest. Version numbers come from the project's manifest, never from this example.

### Filled-in configuration table

~~~~markdown
## Configuration

Variable names are listed in `.env.example`.

| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | Connection string for the primary database | yes |
| `JWT_SECRET` | Signing key for access tokens. Generate a long random value locally. | yes |
| `PORT` | HTTP listen port | no, default `3000` |
~~~~

### Command verification record (goes in Evidence)

~~~~text
README commands verified in a fresh clone:
  npm ci                 exit 0
  cp .env.example .env   exit 0
  npm run db:migrate     exit 0 (local test database only)
  npm run dev            started; "Listening on http://localhost:3000" shown
  npm test               exit 0 (148 passed)
Not run: npm run deploy (remote-writing; needs user approval)
~~~~

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Documenting a command from memory | New readers hit an error on step one | Run it in a clean checkout and record the result |
| Copying the environment variable list into prose | The two lists drift apart | List names in `.env.example`, link or table once in the README |
| Leaving template links to missing docs | Broken links erode trust in the whole README | Remove the link or report the missing doc to the architect |
| Putting real values in examples | Leaks secrets and hostnames | Use placeholders such as `<DATABASE_URL>` |
| Multiple setup paths in the quick start | Readers cannot tell which one is supported | One path in the quick start, alternatives in a how-to guide |
| Running a documented reset command to test it on a shared database | Destroys data | Verify against a local test database or label `not run` |
| Pasting a full option list into Usage | Goes stale and buries the example | Show the common case and link to the reference |
| Choosing a licence or adding a contact address unasked | Legal and personal decision | Ask the user; add only what exists |
| Using absolute links to the repository's own files | Break in clones and on other branches | Use relative links |
| Adding a Windows variant you did not run | Unverified commands mislead | Label it `not run` or omit it |

## Checklist

- [ ] The README keeps the template's section order and adds no section the project does not need.
- [ ] The purpose sentence states what the project does and for whom.
- [ ] Every runtime version in `Requirements` matches the manifest or version file.
- [ ] Every command was run in a clean state, or is labelled `not run` with the reason.
- [ ] Every step that has a visible result states it.
- [ ] Every destructive or remote-writing command carries a warning and was not run without approval.
- [ ] Test, lint and build commands match the `Commands` line in `AGENTS.md` and the manifest scripts.
- [ ] Every environment variable the code reads appears in `.env.example` and in the Configuration table.
- [ ] The README contains no secrets, real hostnames or personal data.
- [ ] Every relative link resolves and every `Documentation` entry points at a file that exists.
- [ ] Reference and explanation content longer than a short paragraph was moved to `docs/` and linked.
- [ ] `CHANGELOG.md` was checked for a matching entry.

## Verify with context7 and gh_grep

- **context7:** query the documentation of every CLI and tool whose command or flag the README uses, at the version in the lockfile. Examples: `<package manager> install from lockfile command`, `<package manager> run script syntax`, `<framework> start development server command`, `<container tool> compose up flags`. Confirm GitHub's current README behaviour (relative links, table of contents, size limit) in GitHub's documentation.
- **gh_grep:** search literal text to see how maintained projects structure a quick start. Examples: `## Quick start`, `cp .env.example .env`, `## Requirements`, `## Configuration`. Prefer official documentation when a repository example disagrees.

## Sources

- About READMEs (GitHub Docs): https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- Diátaxis, start here: https://www.diataxis.fr/start-here/
- Diátaxis, tutorials: https://www.diataxis.fr/tutorials/
- Diátaxis, how-to guides: https://www.diataxis.fr/how-to-guides/
