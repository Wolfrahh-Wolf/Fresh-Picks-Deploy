# CI/CD Pipelines

Covers building, testing and deploying with GitHub Actions: workflow structure, job permissions, secrets management, caching, OIDC cloud credentials, action pinning and quality gates; based on GitHub Actions documentation (2026), checked 2026-11-26.

## Contents

- Workflow structure and triggers
- Permissions: least privilege per job
- Secrets and GitHub Environments
- OIDC for cloud credentials
- Caching dependencies
- Pinning third-party actions
- Quality gates and pipeline structure
- Deployment jobs and approvals

## Guidance

### Workflow structure and triggers

Store workflows in `.github/workflows/`. Use descriptive filenames: `ci.yml` for build/test, `release.yml` for tagging and publishing, `deploy.yml` for environment deploys.

Trigger rules:
- `push` to `main` and `pull_request` targeting `main` for the CI workflow.
- `push` with a tag pattern (`tags: ['v*']`) for the release workflow.
- `workflow_dispatch` for manual deploys (required by `AGENTS.md` Approval gates — a human must trigger the deploy, not an automatic event).

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

Keep jobs small and single-purpose. A job that both runs tests and deploys cannot be re-triggered safely. Separate concerns: `lint` → `test` → `build` → `deploy`.

### Permissions: least privilege per job

Set `permissions: {}` (read-nothing) at workflow level, then add only what each job needs.

```yaml
permissions: {}   # deny all at workflow level

jobs:
  test:
    permissions:
      contents: read       # checkout
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - run: npm test

  release:
    needs: test
    permissions:
      contents: write      # create release and tag
      packages: write      # push to GHCR
    runs-on: ubuntu-latest
```

Never use `permissions: write-all`. Never leave permissions unset (it inherits the repository default, which is often too broad).

### Secrets and GitHub Environments

| Secret scope | When to use |
|---|---|
| Repository secrets | Shared tooling keys used across all environments (e.g. Codecov token) |
| Environment secrets | Credentials scoped to `development`, `staging` or `production`; protected by reviewers |

Always use GitHub Environments for deployment credentials. Configure **Required reviewers** on the `production` environment so no code path auto-deploys to production without a human approving the job.

Reference secrets safely:

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://example.com
    steps:
      - run: deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}   # scoped to production environment
```

Never echo or `cat` secret values in a step. Never store secrets in environment files committed to the repository.

### OIDC for cloud credentials

Replace long-lived access keys with short-lived OIDC tokens. GitHub acts as an OIDC identity provider; your cloud provider exchanges a workflow JWT for a temporary credential.

```yaml
permissions:
  id-token: write    # required for OIDC token request
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502  # v4.0.2
    with:
      role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
      aws-region: us-east-1
```

Scope the cloud trust policy to the specific repository and environment:

```
"StringLike": {
  "token.actions.githubusercontent.com:sub":
    "repo:your-org/your-repo:environment:production"
}
```

This prevents any other repository or environment from assuming the role.

### Caching dependencies

Use `actions/cache` or the built-in `cache` input on setup actions to avoid re-downloading packages on every run.

```yaml
- uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020  # v4.4.0
  with:
    node-version: 22
    cache: npm              # built-in cache; hashes package-lock.json

- run: npm ci
```

For custom cache keys:

```yaml
- uses: actions/cache@5a3ec84eff668545956fd18022155c47e93e2684  # v4.2.3
  with:
    path: ~/.local/share/pnpm/store
    key: ${{ runner.os }}-pnpm-${{ hashFiles('pnpm-lock.yaml') }}
    restore-keys: |
      ${{ runner.os }}-pnpm-
```

Cache key rules:
- Include the lockfile hash so the cache is invalidated when dependencies change.
- Include `runner.os` to prevent cross-OS cache collisions.
- Use `restore-keys` as a fallback for a partial match.

### Pinning third-party actions

Using a mutable tag (`@v4`) means the action's code can change under you. Pin to the full-length commit SHA of the exact release you have reviewed.

```yaml
# Bad
- uses: actions/checkout@v4

# Good
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
```

Add a comment with the version tag so the pin is human-readable. Automate SHA updates with Dependabot or Renovate:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

### Quality gates and pipeline structure

```
PR opened / push to main:
  lint → unit-tests → integration-tests → build-image → scan-image

Push of release tag (v*):
  CI (above) → create-release → publish-image → deploy-staging

Manual dispatch (production):
  deploy-production   (requires environment reviewer approval)
```

Each stage must succeed for the next to run (`needs: [previous-job]`). Never auto-merge to main without lint and tests passing.

Block merge on:
- Any test failure.
- `trivy` scan finding unfixed CRITICAL or HIGH CVEs.
- `spectral lint` errors (if the project has an OpenAPI spec).

### Deployment jobs and approvals

Deployment to production must require manual approval per `AGENTS.md` Approval gates. Use `workflow_dispatch` or a manually triggered job with an `environment` that has required reviewers.

```yaml
deploy-production:
  needs: [deploy-staging]
  environment:
    name: production
    url: ${{ steps.deploy.outputs.url }}
  runs-on: ubuntu-latest
  steps:
    - name: Deploy
      id: deploy
      run: ./scripts/deploy.sh
      env:
        TARGET: production
```

After deploy, run a smoke-test step (HTTP check against the production health endpoint) in the same job. If the smoke test fails, the job fails and monitoring alerts fire (see `monitoring.md`).

## Examples

### Minimal CI workflow

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions: {}

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020  # v4.4.0
        with:
          node-version: 22
          cache: npm

      - run: npm ci
      - run: npm run lint
      - run: npm test

  build-image:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: Build image
        run: docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .

      - name: Scan image
        uses: aquasecurity/trivy-action@a20de5420d57c4102486cdd9349b532415f2b8b7  # v0.26.0
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
          ignore-unfixed: true

      - name: Push image
        if: github.ref == 'refs/heads/main'
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | \
            docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| `permissions: write-all` at workflow level | Every job has write access to contents, packages, PRs, etc. | Set `permissions: {}` at workflow level; grant per job only what is needed |
| Repository secrets for production credentials | Readable by any workflow; accessible to any user with write access | Use GitHub Environments with required reviewer protection |
| Mutable action tags (`@v4`) | Tag can be repointed; malicious action update silently changes your pipeline | Pin to full-length SHA; annotate with version tag in a comment |
| Combining lint, test and deploy in one job | A deploy cannot be re-triggered without re-running tests; partial failures are ambiguous | Separate into distinct jobs with `needs:` dependencies |
| Auto-triggering production deploys on push | Production changes deploy without human review | Use `workflow_dispatch` or an `environment` with required reviewers |
| Storing `npm ci` output without a cache | Every run downloads packages from scratch; slow and flaky on network issues | Use `actions/setup-node` with `cache: npm` or `actions/cache` |

## Checklist

- [ ] `permissions: {}` set at workflow level; each job has only the permissions it needs.
- [ ] Production secrets are in a GitHub Environment with at least one required reviewer.
- [ ] OIDC used for cloud credentials; no long-lived access keys in secrets.
- [ ] All third-party actions are pinned to full-length SHAs.
- [ ] Dependabot or Renovate is configured to update action SHAs weekly.
- [ ] Image scan (`trivy`) runs before push and exits non-zero on unfixed CRITICAL/HIGH.
- [ ] Production deploy is triggered manually (not on automatic `push`).
- [ ] Smoke test runs in the deploy job after deployment.

## Verify with context7 and gh_grep

- **context7:** Resolve `actions/checkout`, `actions/cache`, `actions/setup-node` SHAs for the latest stable releases. Check: `cache` input options on setup actions, `restore-keys` format, `environment` and `url` output syntax in job definitions.
- **gh_grep:** Search `permissions: {}` with `permissions: contents: read` for per-job scoping patterns; `environment: production` with `needs:` for gated deploy patterns; `role-to-assume: arn:aws:iam` for OIDC wiring; `ignore-unfixed: true` in trivy-action config.

## Sources

- GitHub Actions documentation: https://docs.github.com/en/actions
- GitHub Actions security hardening: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- GitHub OIDC with cloud providers: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments
- Trivy action: https://github.com/aquasecurity/trivy-action
