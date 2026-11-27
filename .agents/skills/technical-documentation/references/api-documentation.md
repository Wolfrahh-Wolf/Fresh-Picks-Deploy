# API Documentation

How to write human-facing API reference and guides, give runnable examples, and keep them in step with `docs/API-CONTRACTS.md`, including the Diátaxis page-type rules that every RelayCrew document follows; assumes HTTP APIs with JSON bodies, Diátaxis as published at diataxis.fr, and an OpenAPI or GraphQL schema where the project has one, checked 2026-11-26. The project's own conventions win.

## Contents

- The four page types (Diátaxis)
- Who owns which API document
- Reference entries
- Guides and tutorials
- Examples that run
- Errors, auth, pagination and limits
- Keeping docs in step with the contract
- Generated reference and schemas
- Changes, deprecations and breaking changes

## Guidance

### The four page types (Diátaxis)

Diátaxis separates documentation by what the reader needs. Decide the type before writing a page, then keep the page to that type.

| Type | Reader's need | Write it as | Leave out |
|---|---|---|---|
| Tutorial | Learn by doing | A guided lesson with a visible result at each step, minimal explanation, one path | Options, alternatives, background, generalisation |
| How-to guide | Get a specific job done | Steps toward one real goal, for a competent reader, titled "How to ..." | Teaching, exhaustive options, digressions |
| Reference | Look up facts while working | Neutral, complete, consistent description that mirrors the structure of the thing described | Instructions, opinion, background, marketing |
| Explanation | Understand why | Context, reasons, alternatives and trade-offs, titled so "About ..." fits in front | Steps and fact tables |

The compass question, applied to any piece of content: does it inform an action or knowledge, and does it serve study or work? Action for study is a tutorial. Action for work is a how-to guide. Knowledge for work is reference. Knowledge for study is explanation.

Where the RelayCrew documents sit:

| Document | Type | Note |
|---|---|---|
| README quick start | Tutorial | One path, visible result per step |
| README usage snippets, API guides | How-to | One goal each |
| `docs/API-CONTRACTS.md`, README configuration table | Reference | Facts only |
| `docs/ARCHITECTURE.md`, `docs/DESIGN.md` principles | Explanation | Keep reasons apart from component tables |
| Component tables, `docs/DB.md` table list, design tokens | Reference | Mirror the system |
| `CHANGELOG.md` | A dated record | Outside the four types. Keep it factual |

When a page mixes types, split it or move the foreign part to its own page and link. The common failure is explanation leaking into reference and instructions leaking into explanation.

### Who owns which API document

- `docs/API-CONTRACTS.md` is the contract and is owned by the architect. It states intent: inputs, outputs, errors, permissions. For contract design and OpenAPI authoring, load `api-engineering`.
- Human-facing guides, runnable examples and the README endpoint list are onboarding documentation. The implementer owns them. If the project has no guides location, put short guides in the README `Usage` section. Longer ones go in a `docs/guides/` folder only if the project already uses one. Otherwise report the need to the coordinator rather than starting a new documentation area.
- The implementer never edits `docs/API-CONTRACTS.md`. When code changes an endpoint, name the endpoint and the difference in `Docs impact` for the architect.
- The architect never edits the README or the changelog. When a contract change needs a guide or example update, name it in `Docs impact` for the implementer.

### Reference entries

A reference entry is complete, terse and in the same order everywhere. Use the headings of the `API-CONTRACTS.md` template for every endpoint:

| Field | Must state |
|---|---|
| Purpose | One sentence on what the endpoint does |
| Auth and permissions | Required authentication, scopes or roles; "none" if public |
| Request | Method, path, path and query parameters, headers, body fields with type, required or optional, constraints and defaults |
| Success response | Status code, body fields with type and meaning, headers that matter |
| Errors | Every status the endpoint can return, with its body shape and the cause |
| Compatibility notes | Since which version, deprecation state, behaviour clients must not rely on |

Rules:

1. Group entries by resource or feature, the way the API is organised. Mirror the product.
2. Describe, do not instruct. Put "how to" content in a guide and link to it.
3. Document every response the code can produce, including validation failures, authentication failures, rate-limit responses and server errors. Find them by reading the handler and its middleware, not by guessing.
4. Give each field a type and a constraint, such as a length range, an allowed value set or a format. "string" alone is incomplete.
5. Use one name for one thing. If the code calls it `userId`, the docs call it `userId`.
6. Record units and formats once in the conventions section: time format, money representation, identifier format.
7. Mark open decisions as **open** and unconfirmed behaviour as **unverified**. Never fill a gap with a guess.

The conventions section at the top covers what applies to all endpoints: base path, versioning, authentication, content types, error format, pagination, rate limits and idempotency. Write each once. Endpoint entries then say only what differs.

### Guides and tutorials

- **Getting started tutorial.** One path from nothing to a first successful call. State what the reader will have at the end, give each call with its expected response, and stop. No alternatives.
- **How-to guides.** One goal per guide, titled "How to ...": "How to authenticate and call a protected endpoint", "How to page through results". Assume the reader knows the basics. Start with the goal. Use conditional steps where the path forks. Link to reference entries rather than repeating them.
- **Explanation pages.** "About the authentication model": why tokens expire, why errors do not distinguish unknown email from wrong password. Keep these short and link them from reference.

Name the audience in the first line when it is not obvious: client developers, operators, or internal contributors.

### Examples that run

Every example is a contract with the reader. Apply these rules:

1. **Complete and minimal.** Show the whole request, including the method, URL, required headers and body, and the whole response, including the status line. Omit optional fields unless the example is about them.
2. **Real shapes.** Copy the field names and structure from a run against a local or test instance, then replace values with placeholders.
3. **Placeholders for secrets and hosts.** Use `<ACCESS_TOKEN>`, `<API_TOKEN>` and a local base URL such as `http://localhost:3000`. No real tokens, production hostnames, customer data or personal data.
4. **One success and the important failures.** Show one success example and the failure a client is most likely to hit first, such as the authentication error.
5. **Run it.** Run each example against a local or test instance, never production. If it cannot be run, label it `not run` and say why. Update the example when the response changes.
6. **State the format.** Name the content type for bodies. Use a language tag on every fenced block.
7. **Version-accurate.** Show the flags and options of the tool you use in the example only after checking them against the tool's documentation.

### Errors, auth, pagination and limits

- **Errors.** Document the common error body once. For each endpoint list status, error code or message, cause and what the client should do. Say which errors are retryable.
- **Authentication.** Say how to obtain a credential, how to send it, how long it lasts and what happens on expiry. Security properties and attack testing belong to `security-engineering`.
- **Pagination.** State the parameters, default and maximum page size, ordering guarantees and how the end of the list is signalled.
- **Rate limits.** State the limit, the scope (per IP, per credential), the response when exceeded and which headers report remaining quota, if any.
- **Idempotency.** State which operations are safe to retry and how a client makes a retry safe.

### Keeping docs in step with the contract

The contract states intent. The code is behaviour. The documentation describes behaviour that matches the contract. If they differ, `AGENTS.md` is explicit: report the difference and ask which is right. Never change documentation or the contract silently to hide it.

Drift check, run whenever an endpoint, validation rule, error or permission changes:

1. **Build the inventory from the code.** Use the framework's own route listing or generated schema document if it has one (verify how with context7). Otherwise search the code for route registrations.
2. **Compare with the docs.** List endpoints that exist in code and not in docs, in docs and not in code, and any with a different method or path.
3. **Compare each changed endpoint field by field.** Check request fields, validation limits, success shape, every error status, the auth requirement and the rate limit.
4. **Run the examples** against a local or test instance and compare the real response with the documented one.
5. **Classify each difference.** The code is wrong against an approved contract: report to the coordinator as a defect. The contract is stale: report so the architect updates it. Unknown: ask.
6. **Record the result** in `Docs impact`, naming each endpoint touched.

Order of work on a new or changed endpoint: the architect records or updates the contract first, the implementer builds to it and writes the guide and examples from the working endpoint, then docs sync confirms all three agree.

### Generated reference and schemas

- If the project keeps an OpenAPI document or a GraphQL schema, that file is the machine-readable source. The prose contract and guides must not contradict it. Link to it from `docs/API-CONTRACTS.md` instead of copying its content. Authoring and design of the schema belong to `api-engineering`.
- Generated reference helps accuracy but is not sufficient alone. Add the hand-written parts a generator cannot supply: the getting-started tutorial, how-to guides and explanation.
- Never edit generated output by hand. Change the source and re-run the generator, using the command the project documents.
- Commit generated files only if the project already does.
- For events and webhooks, document each event with the same reference fields: trigger, payload fields, delivery and retry behaviour, and an example payload.

### Changes, deprecations and breaking changes

- A new, changed or removed endpoint is a changelog event. The rules and format are in [changelog.md](changelog.md).
- Mark a deprecated endpoint in its Compatibility notes: since which version, what replaces it, when it will be removed.
- A change that makes existing clients fail is breaking. Mark it in the contract's Compatibility notes and in the changelog with `**Breaking:**`. Versioning policy belongs to `api-engineering`.

## Examples

### Filled-in reference entry (the architect's contract)

The endpoint is illustrative.

~~~~markdown
### `POST /api/auth/login`

- Purpose: Exchange an email and password for a short-lived access token.
- Auth and permissions: none (public). Rate limited to 5 attempts per IP per minute.
- Request: `Content-Type: application/json`.
  - `email` (string, required): valid email address, at most 254 characters.
  - `password` (string, required): 1 to 128 characters.
- Success response: `200 OK`, `application/json`.
  - `token` (string): signed access token.
  - `expiresIn` (integer): lifetime in seconds. `900`.
- Errors:
  - `401`: `{ "error": "Invalid credentials" }`. Unknown email or wrong password. The response does not distinguish them.
  - `422`: `{ "errors": { "<field>": "<message>" } }`. Missing or malformed input.
  - `429`: too many attempts. Retry after the window ends.
- Compatibility notes: since v1.0. Refresh tokens are out of scope.
~~~~

### Filled-in how-to guide (the implementer's guide)

~~~~markdown
## How to sign in and call a protected endpoint

Use this when you have an account and want to call an endpoint that needs a token.

1. Request a token:

   ```bash
   curl -s -X POST http://localhost:3000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"<EMAIL>","password":"<PASSWORD>"}'
   ```

   A successful response is `200` with `{"token":"<ACCESS_TOKEN>","expiresIn":900}`.

2. Send the token on every later request:

   ```bash
   curl -s http://localhost:3000/api/me -H "Authorization: Bearer <ACCESS_TOKEN>"
   ```

3. If a call returns `401` after some time, the token expired. Repeat step 1.

If step 1 returns `429`, wait one minute. The limit is described in the
[authentication section of the contract](API-CONTRACTS.md).
~~~~

### Bad to good: example response

Bad: `Returns the token.`

Good: the full response, including status, content type and body, copied from a local run and with values replaced by placeholders, as in the guide above.

### Drift-check record (goes in Evidence)

~~~~text
Endpoints in code: 14. In API-CONTRACTS.md: 13.
Missing from contract: POST /api/auth/logout (reported to architect).
POST /api/auth/login: contract and code agree on fields, 401, 422, 429.
Examples run against local instance: login 200, login 401, login 429. All match.
Not run: GET /api/me example (needs seeded user; documented from handler source).
~~~~

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Documenting the happy path only | Clients cannot handle failures | List every status the handler can return |
| Instructions inside reference entries | Mixes types, bloats lookups | Move steps to a guide and link |
| Examples never run | Fields drift from reality and mislead | Run each against a local instance and copy the real shape |
| Editing the contract to match the code, or the reverse, silently | Hides defects and erases intent | Report the difference and ask |
| Real tokens or production hostnames in examples | Leaks secrets and invites misuse | Use `<ACCESS_TOKEN>` and `http://localhost:3000` |
| Hand-editing generated reference | The next generation overwrites it | Change the source and regenerate |
| Typeless fields such as "string" with no limits | Clients cannot validate before sending | State type, constraint and default |
| Several names for one field | Readers cannot search or trust it | Use the code's name everywhere |
| Implementer edits `API-CONTRACTS.md` | Breaks ownership and bypasses the design owner | Name the change in `Docs impact` for the architect |
| A tutorial with option lists | The learner loses the thread | One path, options to a how-to guide |

## Checklist

- [ ] Each page serves one Diátaxis type and its title fits that type.
- [ ] Every endpoint entry has purpose, auth, request, success response, errors and compatibility notes.
- [ ] Every status the code can return for each endpoint is documented.
- [ ] Each field has a type and a constraint.
- [ ] Conventions (base path, auth, error format, pagination, rate limits, idempotency) are written once.
- [ ] Each example was run against a local or test instance, or is labelled `not run` with the reason.
- [ ] Examples contain only placeholders for tokens, credentials and hosts.
- [ ] The endpoint inventory from the code matches the docs, or every difference is reported.
- [ ] No document was edited by a role that does not own it.
- [ ] Generated files were regenerated, not edited by hand.
- [ ] Deprecations name the replacement and the removal version, and breaking changes are marked `**Breaking:**` in the changelog.

## Verify with context7 and gh_grep

- **context7:** for the project's web framework, query how to list registered routes or emit an OpenAPI document at the version in the lockfile, for example `<framework> list registered routes` and `<framework> generate OpenAPI schema`. Query the documentation of the HTTP client tool used in examples for its exact flags, for example `curl --header option` and `curl --data option`. Query the project's documentation generator's configuration keys before documenting them.
- **gh_grep:** search literal text to see how maintained API docs are laid out, for example `## Authentication`, `## Errors`, `"error":` in `*.md` files, and `Authorization: Bearer <` in documentation. Prefer official documentation when a repository example disagrees.

## Sources

- Diátaxis, start here: https://www.diataxis.fr/start-here/
- Diátaxis, tutorials: https://www.diataxis.fr/tutorials/
- Diátaxis, how-to guides: https://www.diataxis.fr/how-to-guides/
- Diátaxis, reference: https://www.diataxis.fr/reference/
- Diátaxis, explanation: https://www.diataxis.fr/explanation/
