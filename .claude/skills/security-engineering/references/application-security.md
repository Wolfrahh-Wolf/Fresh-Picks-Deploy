# Application Security

Audit and review guidance for input handling, output encoding, injection, CSRF, SSRF, file upload and secure defaults in web applications; assumes OWASP Top 10:2025 and ASVS 5.0.0, checked 2026-11-26. The project's manifest and framework version decide which built-in protections exist.

## Contents

- Tracing untrusted input to sinks
- Input handling
- Output encoding and cross-site scripting
- Injection (SQL, NoSQL, commands, templates, paths, XML)
- Cross-site request forgery
- Server-side request forgery
- File upload
- Redirects, deserialisation and other sinks
- Secure defaults

## Guidance

### Tracing untrusted input to sinks

This is the core audit move. Do it for every entry point in scope.

1. List sources: request body, query, path parameters, headers, cookies, uploaded files and names, webhook payloads, queue messages, data read from a store another process can write, responses from third-party services, environment and command-line arguments.
2. List sinks: database queries, shell and process calls, file system paths, template engines, HTML or script output, outbound HTTP requests, redirects, deserialisers, log writers, eval-like functions.
3. Follow each source to each sink through the code. Record what validation, transformation and encoding happens in between.
4. A source that reaches a sink with no control that fits the sink is a candidate finding. Confirm with the file and line before you report it.

Defence belongs at the sink: validation narrows what is accepted, but the sink-specific control (parameterisation, encoding, argument arrays) is what makes it safe.

### Input handling

- Validate on the server for type, length, range, format and allowed values, as early as possible at the boundary. Client-side validation is a usability feature, not a control.
- Prefer allowlists (what is permitted) over denylists (what is forbidden). Denylists of "bad characters" are a weakness to report.
- Canonicalise before validating (decode, normalise Unicode, resolve paths), then validate the canonical form, and use that same value afterwards.
- Set size limits for bodies, fields, arrays, nesting depth, and file sizes. Missing limits belong under resource consumption; see [api-security.md](api-security.md).
- Reject unexpected fields rather than ignoring them when the data feeds an object update (see mass assignment in [api-security.md](api-security.md)).
- Handle missing and extra parameters explicitly; failure to do so is part of A10:2025 in [owasp-top-10.md](owasp-top-10.md).
- Validation schema design for API contracts: load `api-engineering`.

### Output encoding and cross-site scripting

- Encode at output for the exact context: HTML body, HTML attribute, JavaScript string, URL component, CSS. One encoder does not fit all contexts.
- Use the framework's automatic escaping and audit every escape hatch. Search the code for the raw-render features of the framework in use: `dangerouslySetInnerHTML` (React), `v-html` (Vue), `|safe` or `autoescape false` (Jinja), `innerHTML` and `insertAdjacentHTML` (DOM), raw output tags in server templates.
- Where user-supplied HTML must be rendered, require a maintained sanitiser configured with an allowlist, applied at output, and require a Content Security Policy as a second layer.
- Never place untrusted data inside script blocks, event-handler attributes or inline styles.
- Do not store session tokens where scripts can read them (see [authentication-security.md](authentication-security.md)); cookie attributes limit the impact of a script injection but do not replace encoding.

### Injection

| Sink | Expected control | Report when |
|---|---|---|
| SQL | Bound parameters for every value; identifiers (table, column, sort direction) from an allowlist | Queries built by string concatenation or formatting, including inside ORM raw-query escape hatches |
| NoSQL | Typed validation so operators cannot arrive from input; no query objects built from the raw body | A request body is passed straight into a query filter |
| OS command | No shell; fixed executable; argument array; allowlisted arguments | A shell string is built from input, or `shell=True` style options are used with input |
| Template engine | Templates are code, loaded from trusted files | User text is compiled as a template |
| LDAP, XPath | Parameterised APIs or context-specific escaping | Filters built by concatenation |
| File path | Resolve the final path and confirm it lies under the intended base | A user-supplied name or path is joined and opened without the containment check |
| XML | Parser configured to refuse external entities and DTDs unless required | Default parser settings of a library whose defaults allow entity expansion (confirm with context7 for the version) |

ORM caution: ORMs parameterise their query builders, but raw-query helpers and string interpolation into `order by`, `limit` or column names are injection points.

### Cross-site request forgery

- A state-changing request authenticated by a cookie needs protection: a synchronised or signed anti-forgery token, or a verified `Origin` check, plus a deliberate `SameSite` value on the session cookie.
- `SameSite` is defence in depth, not a replacement for a token. A JSON API that authenticates with a cookie is still exposed.
- State-changing operations must not use GET.
- APIs that authenticate only with a bearer token in a header (not a cookie) are not CSRF-prone through the browser's automatic cookie sending, but report any fallback that also accepts a cookie.
- CORS is not a CSRF control. Check that allowed origins are an explicit list and that credentials are never allowed with a wildcard.
- Framework-provided protection: confirm it is enabled and not exempted on routes with side effects.

### Server-side request forgery

SSRF means the server fetches a destination an attacker influences, reaching services the attacker cannot (internal hosts, cloud metadata endpoints). In the 2025 list it falls under A01; for APIs it is API7:2023.

Audit questions: which features fetch a URL (webhooks, image or avatar import, link previews, PDF or screenshot rendering, import-from-URL, OAuth discovery)? Who controls the URL? What can the fetcher reach on the network?

Defences, in order of strength:

1. Avoid fetching user-supplied URLs. Where possible let the user upload the content instead.
2. Allowlist destinations by exact scheme, host and port. Where destinations are truly user-chosen, restrict to public addresses.
3. Resolve the hostname, check that every resulting address is public (not loopback, private, link-local or the cloud metadata address), then connect to the address you checked. Checking a name and then letting the client resolve it again leaves a window for DNS rebinding.
4. Disable redirects or revalidate each hop. Allow only `https` unless there is a documented need.
5. Set short connect and read timeouts and response size limits.
6. Block egress at the network layer so the application cannot reach internal services it does not need; see [infrastructure-security.md](infrastructure-security.md).
7. Do not return the raw fetched response or its error text to the caller.

### File upload

Treat every part of an upload as hostile: content, declared type, extension and file name.

- Enforce a maximum size at the web server or framework layer before the body is buffered, plus per-user quotas and counts.
- Allowlist extensions and verify content type by inspecting the content, not the client header. Re-encode images where practical to strip embedded payloads.
- Generate the stored name yourself; never use the supplied name for storage, and sanitise it if it is only displayed.
- Store outside the web root or in object storage with no public listing. Never execute, include or interpret uploaded files. Serve with a fixed, safe content type, `X-Content-Type-Options: nosniff`, and a download disposition for anything not meant to render.
- Check authorization on download exactly as on any other object read (see [authorization-security.md](authorization-security.md)); guessable file identifiers are an access-control finding.
- Remove temporary files on every error path.
- Archives (zip, tar) need entry-count, total-size and path checks before extraction.
- Scan for malware where the data is shared with other users.

### Redirects, deserialisation and other sinks

- Open redirects: redirect only to an allowlist or to relative paths built by the server.
- Deserialisation: do not deserialise untrusted data with formats that can create arbitrary object types; prefer plain data formats with schema validation.
- Dynamic evaluation (`eval`, `Function`, dynamic `require` or `import` of input) with any influence from input is a finding.
- Regular expressions applied to unbounded input can exhaust CPU; check complexity on user-controlled patterns or very long inputs.
- Prototype or object-merge helpers applied to request bodies need key allowlists in languages where merging can alter shared object prototypes.

### Secure defaults

Check that production runs with:

| Area | Expected |
|---|---|
| Errors | Generic message to the client, detail in server logs, debug and stack traces off |
| Cookies | `Secure`, `HttpOnly`, explicit `SameSite`, narrow scope (see [authentication-security.md](authentication-security.md)) |
| Headers | `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, a Content Security Policy fitted to the app, `frame-ancestors` or equivalent clickjacking control, a restrictive `Referrer-Policy` |
| CORS | Explicit origin allowlist; no reflected origin; credentials only with named origins |
| Methods | Only the methods each route needs |
| Admin and debug routes | Absent or restricted to an internal network and authenticated |
| Dependencies' defaults | Reviewed for the installed version (context7), not assumed |

Header middleware ships safe-ish defaults but a Content Security Policy usually needs tuning; confirm the options for the installed version rather than assuming.

## Examples

### SQL: concatenation to bound parameters (Node, `pg`)

```js
// Bad: value interpolated into the statement
const rows = await pool.query(`SELECT id, email FROM users WHERE id = '${req.params.id}'`);

// Good: value bound as a parameter
const rows = await pool.query("SELECT id, email FROM users WHERE id = $1", [req.params.id]);
```

### SQL: SQLAlchemy 2.x raw statement with a bound parameter

```python
from sqlalchemy import text
row = conn.execute(text("SELECT id, email FROM users WHERE id = :id"), {"id": user_id}).first()
```

### OS command: shell string to argument array

```python
# Bad: input becomes part of a shell command line
subprocess.run(f"convert {src} {dst}", shell=True)

# Good: fixed executable, separate arguments, no shell
subprocess.run(["convert", src, dst], check=True, timeout=30)
```

### Path containment

```python
from pathlib import Path

BASE = Path("/srv/uploads").resolve()

def safe_path(name: str) -> Path:
    candidate = (BASE / name).resolve()      # resolves ".." and symlinks
    if not candidate.is_relative_to(BASE):   # Python 3.9+
        raise ValueError("path outside base directory")
    return candidate
```

### SSRF: allowlist and public-address check

```python
import ipaddress, socket
from urllib.parse import urlsplit

ALLOWED_HOSTS = {"api.partner.example"}

def check_destination(raw: str) -> str:
    parts = urlsplit(raw)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise ValueError("destination not allowed")
    for info in socket.getaddrinfo(parts.hostname, parts.port or 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ValueError("non-public address")
    return raw  # then connect to the checked address, with redirects disabled
```

### Finding wording for a raw-render escape hatch

```
[medium] User comment rendered as raw HTML
Location: src/components/Comment.tsx:31
Category: OWASP A05:2025
Evidence: comment.body from GET /api/comments passes to dangerouslySetInnerHTML without sanitising.
Impact: script runs in other users' sessions when they view the comment.
Likelihood: any authenticated user can create a comment.
Remediation: render as text, or sanitise with an allowlist sanitiser at output; add a CSP. Verify with a test that markup in a comment is displayed inert.
Confidence: confirmed
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Relying on client-side validation | Anyone can send requests directly | Validate on the server at the boundary |
| Denylisting "dangerous" characters | Always incomplete; breaks legitimate input | Allowlist by type and format, and use the sink's own defence |
| Parameterising values but concatenating column or sort names | Identifiers remain injectable | Map input to an allowlist of identifiers |
| Validating a name, then letting the client resolve it again for SSRF | DNS can change between check and use | Connect to the address you validated; disable redirects |
| Trusting `Content-Type` or file extension on upload | Both are client-controlled | Inspect content, set your own stored name and type |
| Treating `SameSite` as the whole CSRF defence | Browser behaviour varies; same-site attacks remain | Use anti-forgery tokens or origin checks as well |
| Encoding once for every context | Wrong context leaves injection open | Encode for HTML, attribute, script, URL separately, via the framework |
| Returning fetched content or errors from a URL fetcher | Gives an internal-network oracle | Return a generic result; log detail |

## Checklist

- [ ] Every source in scope was traced to every reachable sink.
- [ ] Every database query uses bound parameters, and identifiers come from allowlists.
- [ ] No shell strings are built from input.
- [ ] Every raw-render escape hatch was searched for and justified or reported.
- [ ] State-changing cookie-authenticated routes have CSRF protection.
- [ ] Every feature that fetches a user-influenced URL has destination controls and egress limits.
- [ ] Uploads have size limits, content checks, generated names, safe storage and authorized download.
- [ ] Redirect targets are allowlisted or server-built.
- [ ] Production error responses are generic.
- [ ] Security headers and CORS were checked against the installed framework version.

## Verify with context7 and gh_grep

- **context7:** for the framework and version in the lockfile, query: "output escaping and raw HTML rendering", "CSRF protection configuration", "parameterised queries and raw SQL", "file upload size limits", "security header middleware options", "XML parser external entity settings". Confirm each default before marking a protection present.
- **gh_grep:** search literal code: `dangerouslySetInnerHTML`, `shell=True`, `rejectUnauthorized: false`, `verify=False`, `.is_relative_to(`, `allow_redirects=False`, `X-Content-Type-Options`. Compare how maintained projects bound upload sizes and validate destinations before recommending an approach.

## Sources

- OWASP Top 10:2025, A01 Broken Access Control (SSRF now within A01; CSRF and path traversal CWEs): https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/
- OWASP Top 10:2025, A10 Mishandling of Exceptional Conditions (resource release, fail closed): https://top10.owasp.org/2025/A10_2025-Mishandling_of_Exceptional_Conditions/
- OWASP Top 10:2025 Introduction (Injection category scope): https://top10.owasp.org/2025/0x00_2025-Introduction/
- OWASP Session Management Cheat Sheet (cookie attributes, SameSite as defence in depth, Cache-Control): https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Top 10 API Security Risks 2023 (API7 SSRF): https://owasp.org/API-Security/editions/2023/en/0x11-t10
- OWASP ASVS repository (requirement id format, example 1.2.5 OS command injection): https://github.com/OWASP/ASVS
