# Docker Compose

Covers writing production-quality Compose files: service definitions, health checks, `depends_on` conditions, named volumes, isolated networks, profiles and the differences between local-dev and production usage; based on Docker Compose v2 (the `docker compose` plugin, file format without `version:` key), checked 2026-11-26.

## Contents

- File format and version
- Service definitions
- Health checks and startup ordering
- Volumes
- Networks
- Profiles
- Local development vs. production differences

## Guidance

### File format and version

Use the filename `compose.yaml` (preferred) or `docker-compose.yaml`. In Compose v2, the top-level `version:` key is obsolete; omit it. All features used here are available in the v2 plugin (`docker compose`, not the deprecated `docker-compose` v1 binary).

Validate before every use:

```bash
docker compose config --quiet   # exits 0 if valid, prints merged config
```

### Service definitions

Each service is a named block under `services:`. Minimum required fields:

| Field | Required | Purpose |
|---|---|---|
| `image` or `build` | Yes (one) | Source: pre-built image or build context |
| `restart` | Recommended | `unless-stopped` for persistent services; `no` for one-shot tasks |
| `environment` | As needed | Inject config (use `env_file` to avoid inline secrets) |
| `ports` | As needed | Expose to host; omit for services only on internal network |
| `depends_on` | As needed | Control start ordering; use `condition` for health-based waits |

Always use `restart: unless-stopped` for long-running services so the container recovers from crashes without manual intervention. Use `restart: no` for migration or seeding one-shot services.

### Health checks and startup ordering

Containers that are "running" are not necessarily "ready". Health checks distinguish the two states and prevent dependent services from connecting to an unready process.

```yaml
services:
  db:
    image: postgres:17-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s   # grace period before the first check counts
```

Use `depends_on` with `condition: service_healthy` to block a service until its dependency is healthy:

```yaml
  api:
    build: .
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

Three dependency conditions:

| Condition | Meaning |
|---|---|
| `service_started` (default) | Container has started; no health guarantee |
| `service_healthy` | Healthcheck has passed at least once |
| `service_completed_successfully` | One-shot container exited 0 (use for migrations) |

For the web service's own health check, use a lightweight probe:

```yaml
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider",
             "http://localhost:8080/healthz"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 20s
```

Start CI or automated tests with `docker compose up --wait --wait-timeout 90` to block until all services are healthy before running tests.

### Volumes

Named volumes persist data across `docker compose down`. Never use anonymous volumes for data you need to retain.

```yaml
services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data   # named volume (persistent)
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro   # bind mount (read-only)

volumes:
  pgdata:
    driver: local
```

**Bind mounts** (host path `./src:/app/src`) are useful for local development hot-reload but must not be used in production — the host path is not available on a remote host or in CI.

`docker compose down` preserves named volumes. `docker compose down -v` deletes them. Never run `down -v` in a shared environment without user confirmation — it destroys persistent data.

### Networks

By default, Compose creates a single default bridge network. All services join it and can reach each other by service name. For stronger isolation, define explicit networks:

```yaml
services:
  api:
    networks: [frontend, backend]
  db:
    networks: [backend]       # db is not reachable from services on frontend only
  nginx:
    networks: [frontend]

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true            # no egress from backend to the internet
```

`internal: true` prevents network egress, which is useful for database or cache networks that should never be reachable from outside the cluster.

### Profiles

Profiles gate services so they are only started when explicitly requested. Use them for:

- Database admin UIs (Adminer, pgAdmin) — available to developers but not in CI.
- Debugging sidecars.
- Load generators or integration test helpers.

```yaml
services:
  adminer:
    image: adminer:4
    profiles: [tools]
    ports: ["8081:8080"]
    networks: [backend]
    depends_on: [db]
```

Activate a profile:

```bash
docker compose --profile tools up -d
```

Standard `docker compose up` starts only services with no `profiles` key (or `profiles: []`).

### Local development vs. production differences

Never use a single Compose file that serves both purposes equally. Split configuration:

| Purpose | File | Characteristics |
|---|---|---|
| Shared base | `compose.yaml` | Service names, networks, volumes, health checks |
| Local overrides | `compose.override.yaml` | Bind mounts for hot-reload, exposed ports, debug profiles |
| CI overrides | `compose.ci.yaml` | Pinned image tags, no bind mounts, test commands |

Compose automatically merges `compose.yaml` and `compose.override.yaml` on `docker compose up`. For CI use an explicit merge: `docker compose -f compose.yaml -f compose.ci.yaml up`.

**Local-only patterns** (never in production):
- Bind-mounting source directories for hot-reload.
- Exposing database ports to the host (`5432:5432`).
- Running with `restart: no` for fast iteration.
- Using `profiles` for local tools.

**Parity rules** (must match between local and production):
- Same image, same environment variable names and defaults.
- Same network topology (which services can talk to which).
- Same health-check commands.

## Examples

### Complete local-dev Compose file

```yaml
# compose.yaml

services:
  db:
    image: postgres:17-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-appuser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?DB password required}
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks: [backend]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-appuser}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s

  api:
    build:
      context: .
      target: runtime
    restart: unless-stopped
    env_file: .env
    ports: ["8080:8080"]
    networks: [frontend, backend]
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider",
             "http://localhost:8080/healthz"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 20s

  adminer:
    image: adminer:4
    profiles: [tools]
    ports: ["8081:8080"]
    networks: [backend]
    depends_on: [db]

networks:
  frontend:
  backend:
    internal: true

volumes:
  pgdata:
```

### Running CI tests against Compose services

```bash
docker compose -f compose.yaml -f compose.ci.yaml up --wait --wait-timeout 90 -d
docker compose -f compose.yaml -f compose.ci.yaml run --rm api npm test
docker compose -f compose.yaml -f compose.ci.yaml down -v
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Using `depends_on` without a `condition` | Services start in parallel regardless; API connects before DB is ready | Set `condition: service_healthy` and add a `healthcheck` to the dependency |
| Leaving `version: "3.9"` at the top | Compose v2 ignores it; it causes a warning and signals confusion about the in-use format | Omit `version:` entirely |
| Exposing database ports to the host in non-dev environments | Database is reachable from outside the container network | Remove port mappings for databases in `compose.yaml`; add them in `compose.override.yaml` only |
| Using anonymous volumes (`- /var/lib/postgresql/data`) | Data is lost on `docker compose down`; impossible to manage or back up | Always use named volumes for persistent data |
| Bind-mounting source into production containers | Host source directory is unavailable on a remote host; invalidates the image contract | Bind mount only in `compose.override.yaml` for local dev |
| Running `docker compose down -v` on a shared environment | Destroys all named volumes and their data | Confirm with the user; never run `down -v` on staging or production |

## Checklist

- [ ] No `version:` key at the top of the file.
- [ ] Every long-running service has a `healthcheck` with a meaningful `test`.
- [ ] Every service that depends on a database or cache uses `condition: service_healthy`.
- [ ] Named volumes used for all persistent data; no anonymous volumes.
- [ ] Database ports are not exposed to the host in the shared `compose.yaml`.
- [ ] Dev-only patterns (bind mounts, exposed DB ports, debug profiles) are in `compose.override.yaml`.
- [ ] `docker compose config --quiet` exits 0.
- [ ] `docker compose up --wait` used in CI before running tests.

## Verify with context7 and gh_grep

- **context7:** Resolve the Docker Compose plugin version in the project's CI runner or `devcontainer.json`. Check: `healthcheck` field syntax, `depends_on` condition values, `profiles` array syntax, `internal: true` network field.
- **gh_grep:** Search `condition: service_healthy` for real dependency-ordering patterns; `internal: true` for isolated network usage; `compose.ci.yaml` for CI override file conventions; `--wait --wait-timeout` for CI startup patterns.

## Sources

- Docker Compose documentation: https://docs.docker.com/compose/
- Compose file reference (v2): https://docs.docker.com/reference/compose-file/
