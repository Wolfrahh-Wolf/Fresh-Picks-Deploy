# Environment Management

Covers structuring configuration, injecting environment variables, maintaining environment parity between local, staging and production, and secrets injection patterns; aligned with the Twelve-Factor App methodology (factor III: Config), checked 2026-11-26.

## Contents

- Configuration principles
- Environment variable structure and naming
- Secrets injection
- Environment parity
- Local development setup
- Validating configuration at startup

## Guidance

### Configuration principles

Separate configuration from code. Configuration is anything that varies between deployments (database URL, feature flags, API keys, port numbers). Code does not change between environments; configuration does.

**Rules:**
- Never hard-code environment-specific values in source code or Dockerfiles.
- Never commit `.env` files containing real values to the repository. Commit `.env.example` with placeholder values and explanatory comments.
- Configuration that affects behaviour in production must be testable in staging with the same injection mechanism (not a different code path).

### Environment variable structure and naming

Use UPPER_SNAKE_CASE names. Be consistent across all environments — a name used in staging must be identical in production.

Namespace variables by service when multiple services share a runtime:

```
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
PORT=8080
LOG_LEVEL=info
NODE_ENV=production
```

Classify variables by sensitivity:

| Class | Examples | Storage |
|---|---|---|
| Non-secret config | `PORT`, `LOG_LEVEL`, `NODE_ENV` | Committed to repository in `compose.yaml` or platform config |
| Non-secret secrets (hashes, public keys) | `STRIPE_PUBLISHABLE_KEY` | Environment variable; not in source |
| Secrets | `DATABASE_URL`, `JWT_SECRET`, `STRIPE_SECRET_KEY` | Secret store only; never in `compose.yaml`, CI config or image |

Avoid prefixing every variable with the application name (`MYAPP_PORT`). Use it only when multiple applications share the same environment and variable names would collide.

### Secrets injection

Inject secrets at runtime from a managed store. Never pass secrets through image build args (they appear in `docker history`) or bake them into the image.

**Local development:** `.env` file (git-ignored) loaded by `docker compose` via `env_file: .env`.

**CI:** GitHub Secrets (non-production) or GitHub Environment secrets (production). Reference as `${{ secrets.DATABASE_URL }}` in workflow YAML, never print their value.

**Production (container platforms):** Pull from the platform's native secret store at container startup:

| Platform | Mechanism |
|---|---|
| AWS ECS | Secrets Manager ARN in `secrets:` block of task definition |
| Cloud Run | `--set-secrets` flag maps secret versions to env var names |
| Kubernetes | `secretKeyRef` in pod spec; use sealed secrets or external-secrets-operator |
| Heroku / Render | Platform config vars (encrypted at rest) |

**Secret rotation:** when a secret rotates, the new value must be available in the secret store before restarting the service. With AWS Secrets Manager / GCP Secret Manager, pin to `latest` version for automatic pickup on container restart, or to a specific version for explicit control.

Never log environment variables at startup. Log the names of the variables that were loaded (not their values) so missing config is obvious.

### Environment parity

The local, staging and production environments must be as similar as possible. Differences are a source of bugs that only appear in production.

**What must match:**
- The same Docker image (or build context) — staging and production must use the same Dockerfile and base image.
- The same environment variable names and types.
- The same backing services (same database engine and major version, same cache engine).
- The same networking topology (containers talk to each other by service name; no `localhost` shortcuts).

**Allowed differences:**
- Credentials (different database URL, different API key).
- Resource limits (staging can have fewer replicas and smaller memory limits).
- Feature flags that gate unreleased features.

Maintain a `.env.example` file at the repository root that lists every variable name used anywhere in the application, with a one-line comment explaining each. Keep it up to date as variables are added or removed.

```bash
# .env.example

# Application
PORT=8080
LOG_LEVEL=info           # debug | info | warn | error
NODE_ENV=development     # development | production

# Database
DATABASE_URL=postgresql://appuser:changeme@localhost:5432/appdb

# Auth
JWT_SECRET=<replace-with-32-char-random-string>
JWT_EXPIRY_SECONDS=3600

# Payments (Stripe)
STRIPE_SECRET_KEY=<replace-with-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<replace-with-stripe-publishable-key>
```

### Local development setup

A developer cloning the repository must be able to get running in one command:

```bash
cp .env.example .env     # then fill in real values for local dev
docker compose up
```

Do not require developers to know what values to put in; `.env.example` must have workable defaults for local development (using the local Docker network values, not production credentials).

Provide a `Makefile` or `package.json` scripts for common operations:

```makefile
dev:
    docker compose up --watch

test:
    docker compose run --rm api npm test

reset:
    docker compose down -v && docker compose up -d
```

### Validating configuration at startup

The application must fail fast and loudly if required configuration is missing or malformed. Do not let a missing environment variable surface as a confusing runtime error deep inside the application.

Validate at process startup before accepting any traffic:

```typescript
// config.ts — validated configuration module
import { z } from 'zod';

const ConfigSchema = z.object({
  PORT: z.coerce.number().int().min(1024).max(65535).default(8080),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

const parsed = ConfigSchema.safeParse(process.env);
if (!parsed.success) {
  console.error('Invalid configuration:', parsed.error.flatten().fieldErrors);
  process.exit(1);   // fail fast before accepting connections
}

export const config = parsed.data;
```

This approach also type-checks config access throughout the codebase.

## Examples

### docker-compose env_file usage

```yaml
services:
  api:
    build: .
    env_file:
      - .env               # local development values; git-ignored
    # Do NOT put secrets inline here:
    # environment:
    #   JWT_SECRET: my-secret   ← NEVER do this
```

### GitHub Actions: referencing environment secrets

```yaml
jobs:
  deploy:
    environment: production    # activates production environment secrets
    steps:
      - run: ./scripts/deploy.sh
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Committing `.env` with real values | Credentials exposed in git history permanently; breach is irreversible | Add `.env` to `.gitignore`; commit only `.env.example` with placeholders |
| Passing secrets as Docker `ARG` / `--build-arg` | Secret visible in `docker history` and cached in intermediate layers | Never use build args for secrets; inject at container startup via env vars or secret mounts |
| Using different variable names in staging vs. production | Config differences hide bugs; name mismatches cause silent failures on deploy | Use identical names across all environments; validate with `.env.example` |
| Not validating config at startup | Missing variable causes a cryptic runtime error on first use | Validate the full config schema at startup and exit 1 with a clear message |
| Logging environment variable values on startup | Credentials appear in log archives and monitoring dashboards | Log only variable names (or a startup banner showing which vars were loaded) |
| Hard-coding `localhost` for backing services | Works on the developer's machine; fails in Docker and CI where services are on separate containers | Always use service names (`db`, `redis`) from `compose.yaml`; never `localhost` |

## Checklist

- [ ] `.env.example` is committed and covers every variable the application uses, with comments.
- [ ] `.env` is in `.gitignore`; no real credentials are committed.
- [ ] Secrets are injected at runtime from the platform's secret store; never in image or compose file inline.
- [ ] Variable names are identical across local, staging and production.
- [ ] Application validates all required config at startup and exits non-zero on missing/invalid values.
- [ ] No environment variable values are logged at startup.
- [ ] Backing services are referenced by service name (`db`, `redis`), not `localhost`.

## Verify with context7 and gh_grep

- **context7:** Resolve `zod` at the project's locked version for config validation patterns. Check: `z.coerce.number()`, `z.enum()`, `safeParse` and `flatten().fieldErrors` output format.
- **gh_grep:** Search `env_file: .env` for Compose secret injection patterns; `ConfigSchema.safeParse(process.env)` for startup validation; `secrets.DATABASE_URL` in workflow YAML for GitHub Actions secret usage; `.env.example` with `DATABASE_URL=` for `.env.example` structure.

## Sources

- Twelve-Factor App — Config: https://12factor.net/config
- AWS Secrets Manager in ECS: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html
- Google Cloud Run secrets: https://cloud.google.com/run/docs/configuring/secrets
