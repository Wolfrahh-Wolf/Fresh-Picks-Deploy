---
name: devops-deployment
description: "Use when containerising, configuring CI/CD, managing environments, deploying, releasing, rolling back or monitoring."
---

# DevOps & Deployment

Guides the full delivery pipeline: from containerising an application through CI/CD, environment management and release to rollback and post-deploy monitoring. Every deployment requires explicit user approval before it runs.

## When to use

- Writing or reviewing a Dockerfile or Docker Compose file.
- Setting up or changing a CI/CD pipeline (GitHub Actions or equivalent).
- Configuring environments, secrets or environment variables.
- Planning a release: versioning, tagging, release notes, pre-release checks.
- Executing or rehearsing a rollback.
- Setting up or reviewing health checks, logging, metrics or alerting.

## Do not use for

- Security audit of infrastructure (threat modelling, IAM review): load `security-engineering`.
- Commit conventions and branching strategy: load `git-version-control`.

## Research: context7 and gh_grep

- You MUST consult **context7** before editing any Dockerfile, Compose file, Actions workflow or platform CLI configuration. Check the tool's exact version first. Useful queries: `docker/dockerfile syntax 1 RUN mount cache`, `docker compose healthcheck condition service_healthy`, `actions/checkout pinned SHA`, `actions/cache save restore keys`, `trivy image scan flags`.
- You MUST search **gh_grep** when a CI pattern, Compose configuration or deployment hook is unfamiliar. Useful searches: `--mount=type=cache` in Dockerfiles; `condition: service_healthy` in compose files; `permissions: contents: read` in workflow YAML; `environment: production` with `needs: build` in Actions; `RateLimit-Remaining` or `Retry-After` in deployment scripts.
- RFC semantics, SemVer rules and OpenTelemetry signal definitions need neither tool — use their official specifications.
- If a tool is unavailable, use official documentation and label unconfirmed claims **unverified**. Never put secrets or private code in a query.

## References

Open only what the task needs.

| Read | When |
|---|---|
| [references/docker.md](references/docker.md) | Writing or reviewing a Dockerfile, multi-stage build, image scanning or layer caching |
| [references/docker-compose.md](references/docker-compose.md) | Writing or reviewing a Compose file: health checks, volumes, networks, profiles |
| [references/ci-cd.md](references/ci-cd.md) | Setting up or reviewing a CI/CD pipeline, GitHub Actions workflow, caching or secrets |
| [references/hosting.md](references/hosting.md) | Choosing or configuring a hosting provider: static, container, PaaS or VM |
| [references/environment-management.md](references/environment-management.md) | Configuring environment variables, secrets injection or environment parity |
| [references/release-management.md](references/release-management.md) | Planning a release: semantic versioning, tagging, release notes or pre-release checks |
| [references/rollback.md](references/rollback.md) | Planning or executing a rollback, database migration safety or rollback rehearsal |
| [references/monitoring.md](references/monitoring.md) | Setting up health checks, structured logs, metrics, traces or alerts |

## Workflow

1. **Classify the work by role:**
   - *Implementer*: open the reference(s) for the specific task (Docker, CI/CD, environment, release). Never deploy without user approval (see `AGENTS.md` Approval gates).
   - *Security-auditor*: check `ci-cd.md` (permissions, OIDC, pinned actions), `environment-management.md` (secrets injection, no plaintext), `docker.md` (non-root, image scanning). For infrastructure threat modelling, load `security-engineering`.
   - *Debugger*: open `monitoring.md` to interpret logs, metrics and traces; open `rollback.md` if the system needs to be restored.

2. **Before any infrastructure change**, check `docs/ARCHITECTURE.md` for the target stack and `docs/TASKS.md` for open deployment tasks. Confirm the environment (dev, staging, production) with the user.

3. **Containerise** (if not done): write the Dockerfile following the multi-stage, non-root, minimal-image rules in `docker.md`. Run `docker build` locally and confirm the image starts cleanly.

4. **Configure Compose** for local and staging environments following `docker-compose.md`. Validate with `docker compose config --quiet`.

5. **Set up or update CI/CD**: follow `ci-cd.md`. Pin all third-party action SHAs. Scope permissions per job. Store secrets in GitHub Environments, not repository-level secrets for production.

6. **Manage environments and secrets** per `environment-management.md`. Confirm parity between staging and production before releasing.

7. **Plan the release**: follow `release-management.md`. Run all pre-release checks. Get user approval before tagging and publishing.

8. **Deploy** (requires user approval per `AGENTS.md`): describe the target, risk and rollback plan. Wait for approval. After deploy, run post-deploy verification per `monitoring.md`.

9. **If a rollback is needed**: follow `rollback.md` immediately. Notify the user. Record the incident trigger and resolution in `docs/MEMORY.md`.

## Standards

- Never deploy without explicit user approval; state the target, risk and rollback plan first.
- Containers must run as a non-root user; use a named UID ≥ 10000, not `root` or unnamed `USER appuser` without a UID.
- Multi-stage Dockerfiles only; never ship build tooling (compilers, dev dependencies) in the runtime image.
- Image scanning (`trivy` or equivalent) must run in CI and fail the build on CRITICAL or HIGH CVEs with a fix available.
- CI/CD permissions must be least-privilege per job; set `permissions: {}` at workflow level and elevate per job only.
- Never store secrets in repository-level GitHub Secrets for production; use GitHub Environments with required reviewer protection.
- All third-party GitHub Actions must be pinned to a full-length commit SHA with a version comment.
- Use OIDC for cloud credentials; never store long-lived access keys in secrets.
- Semantic versioning (SemVer 2.0.0): MAJOR for breaking changes, MINOR for new features, PATCH for fixes.
- Migrations must be backward-compatible with the previous release (expand-and-contract pattern); never drop a column in the same release that removes the code reading it.
- Every deployment has a documented, tested rollback path before it runs.
- Structured JSON logs with `level`, `timestamp`, `traceId` and `service` fields; never log secrets or personal data.
- Health endpoints: `/healthz` (liveness) and `/readyz` (readiness) are distinct and exposed on every service.
- Alerts fire on symptoms (error rate, latency SLO breach), not on infrastructure cause (CPU %).

## Verification

- [ ] `docker build` succeeds and `docker run --rm <image> id` shows a non-root UID.
- [ ] `trivy image <image>` returns no unfixed CRITICAL or HIGH CVEs.
- [ ] `docker compose config --quiet` exits 0 with no warnings.
- [ ] CI pipeline passes on a branch; all jobs use scoped `permissions:`.
- [ ] Secrets are stored in GitHub Environments (not repository secrets) for staging and production.
- [ ] Release tag matches the version in the manifest; `CHANGELOG.md` is updated.
- [ ] Post-deploy smoke test against the target environment passes.
- [ ] Rollback procedure is documented and has been run at least once in staging.
- [ ] Health endpoints `/healthz` and `/readyz` return 200 after deploy.

## Output

Report under **Evidence**: `docker build` output, `trivy` scan results, `docker compose config` output, CI run URL, release tag and smoke-test results. Report under **Research**: context7 versions queried, gh_grep patterns searched. Report under **Docs impact**: `docs/ARCHITECTURE.md` if the hosting or infra topology changed (architect); `README.md` for new setup steps (implementer); `CHANGELOG.md` for every release (implementer); `docs/MEMORY.md` for rollback decisions or new deployment pitfalls (coordinator).
