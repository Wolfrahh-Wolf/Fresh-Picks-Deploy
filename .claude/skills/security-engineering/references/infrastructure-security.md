# Infrastructure Security

Audit checks for containers, CI/CD permissions, network exposure, cloud configuration and least privilege, from a security-review standpoint; assumes OWASP Top 10:2025 A02 and A03 and the GitHub Actions secure-use guidance, checked 2026-11-26. Writing Dockerfiles, pipelines and hosting configuration is owned by `devops-deployment`. Container and cloud flags below that were not re-read in this session are marked (unverified).

## Contents

- Audit stance and approvals
- Containers and compose files
- Kubernetes manifests
- CI/CD permissions and pipeline integrity
- Network exposure
- Cloud configuration and identity
- Infrastructure as code
- Environments and hardening baseline

## Guidance

### Audit stance and approvals

Review configuration files statically: Dockerfiles, compose files, manifests, workflow files, infrastructure as code. Safe local commands are read-only ones, such as rendering a compose file to see the resolved configuration, or a dry-run plan from an infrastructure tool that makes no changes (confirm it needs no remote state write or credentials).

Never probe live, production or third-party systems. Do not deploy, apply, change access control, change secrets or alter pipelines; those are gated actions in `AGENTS.md` and the security-auditor never edits. Report the setting, the risk and the recommended change.

Misconfiguration is OWASP A02:2025, which rose to second place because more behaviour is now defined by configuration. Treat configuration as code that deserves review.

### Containers and compose files

| Check | Expect | Report when |
|---|---|---|
| User | Process runs as a non-root user (`USER` set to a named or numeric non-root user) | No `USER`, or `USER root` in the final stage |
| Base image | Minimal image from a trusted source, pinned by digest for production | Floating `latest`, unknown publisher, full OS image with tools the app does not need |
| Build stages | Multi-stage build; build tools and secrets absent from the final image | Compilers, package caches or source in the final stage |
| Secrets | None in layers, build arguments, environment lines or copied files | `ARG`/`ENV` with credentials, `COPY .env`, key files copied in |
| Build context | `.dockerignore` excludes `.git`, env files, key material, local config | No `.dockerignore`, or `COPY . .` without one |
| Privileges | No privileged mode, capabilities dropped to what is needed, no added devices | `privileged: true`, broad capability additions (unverified for exact flags; confirm in the runtime's docs) |
| Docker socket | Not mounted into application containers | Socket volume mounted (gives control of the host's containers) |
| Filesystem | Read-only root filesystem where the app allows, with explicit writable mounts | Writable everywhere without need |
| Ports | Only needed ports published; databases and caches not published, or bound to the loopback address | Data stores published on all interfaces |
| Resources | Memory and CPU limits set | None; one container can exhaust the host |
| Image content | Scanned for known vulnerabilities | No scan (see [dependency-security.md](dependency-security.md)) |
| Updates | Base image refreshed on a schedule | Image unchanged for a long period with known advisories |

For compose files, check `ports:` mappings (a mapping without an address binds all interfaces), `env_file` and `environment` entries for secrets, `network_mode: host`, shared volumes, and which services share networks. Put internal services on an internal network.

### Kubernetes manifests

If the project deploys to Kubernetes, check the workload definitions for: containers running as non-root with privilege escalation disallowed, read-only root filesystem where possible, dropped capabilities, no host namespace or host path mounts, resource limits, service account token mounting disabled where the pod does not call the API, a service account with least-privilege role bindings (no cluster-wide wildcard permissions), network policies that deny by default and allow named flows, secrets mounted from a secrets mechanism rather than in manifests, and images pinned by digest. Confirm field names and defaults for the cluster version with context7.

### CI/CD permissions and pipeline integrity

A pipeline holds secrets and write access to production; a compromised step is a supply chain incident (A03:2025). For GitHub Actions workflows, verified against the GitHub secure-use guidance:

- **Token permissions:** the default `GITHUB_TOKEN` permission should be read-only for contents; elevate per job only as needed. Prefer a workflow-level `permissions: {}` or `contents: read` with justified job-level additions. A job without explicit `permissions` is a finding.
- **Third-party actions:** pin to a full-length commit SHA, verify the SHA belongs to the action's repository, and audit what the action does with the repository and secrets. A tag is acceptable only for a creator you trust, and organisation policy can require SHA pinning.
- **Untrusted pull request content:** workflows triggered by `pull_request_target` or `workflow_run` run with privileged context. Do not check out and run code from the pull request in them. Prefer the unprivileged trigger unless privilege is required.
- **Script injection:** never interpolate attacker-influenced values (issue titles, branch names, pull request bodies, commit messages) directly into `run:` scripts; pass them through environment variables and quote them in the script.
- **Secrets:** only to jobs that need them; environment-scoped secrets with required reviewers for production; no secrets printed (redaction is not guaranteed); anyone with write access to the repository can read repository secrets, so keep CI credentials low-privilege.
- **Cloud credentials:** prefer federated, short-lived credentials issued to the workflow over stored long-lived keys (the job needs the token-issuing permission, `id-token: write`, only for that job).
- **Runners:** self-hosted runners on public repositories or shared with untrusted code are a risk; prefer ephemeral runners.
- **Repository controls:** protected default branch with required review and status checks, restricted who can change workflow files, and code scanning that covers workflows (CodeQL and OpenSSF Scorecards can flag dangerous workflow patterns).
- **Artifacts:** release artifacts built in CI, checksummed, and ideally with provenance (see [dependency-security.md](dependency-security.md)); promotion to production uses the artifact that was tested.

Other CI systems follow the same questions: least-privilege tokens, pinned build components, isolated untrusted code, scoped secrets, protected branches, artifact integrity.

### Network exposure

- Inventory every listening port, public endpoint, load balancer and DNS name in scope from configuration. Compare with what should be public according to `docs/ARCHITECTURE.md`.
- Databases, caches, queues, admin consoles and monitoring dashboards are not reachable from the internet. Management access goes through a private path with authentication.
- Default-deny network rules: inbound only for required ports from required sources; no `0.0.0.0/0` on administration or data-store ports.
- Segment tiers so a compromised web tier cannot reach everything; restrict outbound traffic to what the service needs. Egress controls limit the impact of SSRF and data exfiltration (see [application-security.md](application-security.md)).
- TLS terminates at a known point, and the hop behind it is protected when it crosses a boundary.
- Non-production environments are not publicly reachable with production-like data; check preview and staging hostnames.
- Subdomain and DNS records that point to retired resources can be taken over; flag dangling records when DNS configuration is in scope.

### Cloud configuration and identity

- **Least privilege identity:** workload roles list specific actions and resources. Wildcard actions or resources on production roles are findings; unused permissions are `low`.
- **No human or root credentials for workloads;** each workload has its own identity.
- **Storage:** buckets and containers are private by default, with public access blocks where the provider offers them; any public object has an owner and a reason.
- **Encryption and keys:** encryption enabled for storage and backups, with key access limited (see [data-protection.md](data-protection.md)).
- **Audit logging:** control-plane and data-access logging is enabled, retained and protected; alerts exist for administrative changes.
- **Separation:** production is separated from development and test (accounts, projects or subscriptions) with distinct credentials.
- **Managed services:** know which controls the provider owns and which the project must configure (shared responsibility); record gaps.
- **Spend and quota limits** reduce abuse impact (API4:2023 for paid calls).

### Infrastructure as code

- Review the code as you would application code: no secrets, pinned module and provider versions, reviewed changes.
- Prefer a plan or diff review before apply. Running an apply, destroy or any state-changing command is gated: state the action, target, risk and rollback and ask the user.
- Remote state holds sensitive values; check that it is encrypted, access controlled and not in the repository.
- Policy-as-code or a scanner for infrastructure files helps; adding one is a change that needs approval.

### Environments and hardening baseline

- Production differs from development only in secrets, endpoints and scale. Debug flags, sample data and admin consoles are off in production.
- Unused services, packages and accounts are removed. Default credentials are changed or disabled.
- Time, logging and monitoring are configured the same everywhere that matters.
- Changes to access control, secrets or CI/CD need user approval; propose, never apply.

## Examples

### Dockerfile: bad to good

```dockerfile
# Bad: floating tag, runs as root, copies everything including local env files
FROM node:latest
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]
```

```dockerfile
# Good: pinned base, install from lockfile, non-root, narrow copy
FROM node:<VERSION>-slim@sha256:<DIGEST>
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY src ./src
USER node
CMD ["node", "src/server.js"]
```

### Workflow: bad to good

```yaml
# Bad: broad default token, movable tag, untrusted text interpolated into a script
permissions: write-all
steps:
  - uses: some-org/deploy-action@v2
  - run: echo "Title is ${{ github.event.pull_request.title }}"
```

```yaml
# Good: read-only default, pinned SHA, untrusted value passed as an environment variable
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: some-org/deploy-action@<FULL_COMMIT_SHA> # v2.x.y
      - env:
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: echo "Title is $PR_TITLE"
```

### Compose ports: bad to good

```yaml
# Bad: database published on every interface
ports:
  - "5432:5432"
# Good: loopback only, or no published port and a private network
ports:
  - "127.0.0.1:5432:5432"
```

### Finding: over-broad CI token

```
[high] Deployment workflow runs with write-all token and unpinned third-party action
Location: .github/workflows/deploy.yml:3 and :14
Category: OWASP A03:2025, A02:2025
Evidence: workflow-level `permissions: write-all`; a third-party action referenced by tag; the job also holds the production deploy secret.
Impact: a compromised action or tag change can push code to the repository and read the production secret.
Likelihood: needs compromise of the action or its maintainer account; medium; consequence is severe.
Remediation: set read-only default permissions with job-level additions, pin the action to a full commit SHA, scope the production secret to a protected environment with required reviewers. Changing CI/CD and secrets needs user approval. Verify by reviewing the resolved workflow permissions and a dry run on a branch.
Confidence: confirmed
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Auditing application code only | Misconfiguration (A02) and pipeline compromise (A03) go unseen | Include Dockerfiles, compose, manifests, workflows and IaC |
| Assuming the container is a security boundary by itself | Privileged settings and sockets defeat isolation | Check user, capabilities, mounts and network |
| Publishing database ports "for convenience" | Direct internet exposure of data stores | Bind to loopback or a private network |
| Leaving the default CI token broad | A single compromised step can write to the repository | Read-only default, job-level elevation |
| Pinning to tags for actions and images | Content changes silently | Digest or full SHA |
| Long-lived cloud keys in CI | A leak gives lasting access | Federated short-lived credentials |
| Running apply or deploy commands to "verify" | Changes production without approval | Static review and dry-run plans only; ask first |
| Treating the internal network as safe | One foothold reaches all services | Segment and authenticate service calls |

## Checklist

- [ ] All Dockerfiles, compose files, manifests, workflows and IaC in scope were reviewed.
- [ ] Containers run as non-root, with no privileged mode, no docker socket and no secrets in layers.
- [ ] Base images and CI actions are pinned to digests or full SHAs.
- [ ] `.dockerignore` and `.gitignore` exclude env files, keys and `.git` content.
- [ ] Data stores, caches and admin interfaces are not publicly reachable.
- [ ] Workflow token permissions are read-only by default, with justified job-level additions.
- [ ] No privileged-trigger workflow runs untrusted pull request code, and no untrusted text is interpolated into scripts.
- [ ] CI secrets are scoped and environment-protected; cloud access uses short-lived credentials where possible.
- [ ] Workload identities are least-privilege with no wildcard production permissions.
- [ ] Storage is private by default, with logging and encryption enabled.
- [ ] No deploy, apply, access-control or secrets change was made during the audit.

## Verify with context7 and gh_grep

- **context7:** query the container runtime for "run as non-root, drop capabilities, read-only filesystem options"; the orchestrator for "securityContext fields and network policy"; the CI platform for "GITHUB_TOKEN permissions", "pull_request_target", "OIDC token permissions"; the infrastructure tool for "plan without applying" and "remote state encryption".
- **gh_grep:** search literal code: `permissions:` followed by `contents: read`, `id-token: write`, `pull_request_target`, `USER node`, `cap_drop`, `readOnlyRootFilesystem`, `automountServiceAccountToken`, `127.0.0.1:` in compose files. Compare with maintained projects' workflows and manifests.

## Sources

- GitHub Docs, Secure use reference for GitHub Actions (least privilege, GITHUB_TOKEN read-only default, SHA pinning, pull_request_target and workflow_run caution, script injection, CodeQL and Scorecards): https://docs.github.com/en/actions/reference/security/secure-use
- GitHub Docs, Protect against threats (explicit workflow permissions, pin third-party actions, restrict which actions run): https://docs.github.com/en/code-security/tutorials/secure-your-organization/protect-against-threats
- OWASP Top 10:2025 Introduction (A02 Security Misconfiguration, A03 Software Supply Chain Failures): https://top10.owasp.org/2025/0x00_2025-Introduction/
- OWASP Secrets Management Cheat Sheet (CI/CD, containers and orchestrators, cloud providers sections; least privilege): https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- SLSA specification, security levels (build platform hardening): https://slsa.dev/spec/v1.0/levels
