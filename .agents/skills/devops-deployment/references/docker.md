# Docker

Covers writing production-quality Dockerfiles: multi-stage builds, BuildKit cache mounts, non-root users, minimal base images, image scanning and layer-caching discipline; based on Docker Engine 27.x and BuildKit 0.17.x documentation, checked 2026-11-26.

## Contents

- Dockerfile structure and BuildKit syntax
- Multi-stage builds
- Layer caching and BuildKit cache mounts
- Non-root users and least-privilege runtime
- Minimal base images and image size
- Image scanning

## Guidance

### Dockerfile structure and BuildKit syntax

Always declare the BuildKit frontend at the top of every Dockerfile:

```dockerfile
# syntax=docker/dockerfile:1
```

This pins the Dockerfile syntax to the latest stable `1.x` BuildKit frontend and enables features like `--mount=type=cache` and `--mount=type=secret` without additional configuration. BuildKit is the default builder backend in Docker Engine 23+.

Build with BuildKit explicitly on older engines: `DOCKER_BUILDKIT=1 docker build .`

Use `.dockerignore` to exclude everything that is not needed in the image: `.git`, `node_modules`, `*.md`, local env files. A missing `.dockerignore` sends the entire working tree as build context, invalidating cache on every file change.

### Multi-stage builds

Separate build-time tooling from the runtime image. The runtime stage must contain only what the application needs to run.

Naming stages with `AS <name>` lets later stages copy from them by name and lets BuildKit build only the stages required for the target.

```dockerfile
# syntax=docker/dockerfile:1

# --- build stage ---
FROM node:22-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev
COPY . .
RUN npm run build

# --- runtime stage ---
FROM node:22-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/node_modules ./node_modules
```

Build a specific stage with `docker build --target builder .` to debug the build stage without producing the runtime image.

### Layer caching and BuildKit cache mounts

**Layer order:** place instructions that change least often at the top. COPY the manifest files (`package.json`, `go.mod`, `requirements.txt`) first; run the install; then copy source. This avoids re-running the install on every source change.

**BuildKit cache mounts** persist package-manager caches across builds without baking them into the image layer:

| Package manager | Cache mount target |
|---|---|
| npm / pnpm | `/root/.npm` or `/root/.local/share/pnpm/store` |
| pip | `/root/.cache/pip` |
| Go modules | `/go/pkg/mod` and `/root/.cache/go-build` |
| apt | `/var/cache/apt` and `/var/lib/apt/lists` |

```dockerfile
# Go example
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -o /bin/app ./cmd/server
```

```dockerfile
# apt example (pin packages; never use apt-get upgrade)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates=20230311 \
    && rm -rf /var/lib/apt/lists/*
```

Do not pin to `latest` or use `apt-get upgrade`; pin package versions for reproducibility.

### Non-root users and least-privilege runtime

Containers run as root inside the container namespace by default. A compromised container running as root can escape to the host more easily. Always create and switch to a dedicated non-root user in the final stage.

```dockerfile
FROM node:22-alpine AS runtime

# Use a numeric UID/GID ≥ 10000 to avoid collisions with host UIDs
RUN addgroup -g 10001 -S appgroup \
 && adduser -u 10001 -S -G appgroup appuser

WORKDIR /app
COPY --from=builder --chown=10001:10001 /build/dist ./dist
COPY --from=builder --chown=10001:10001 /build/node_modules ./node_modules

USER 10001:10001
EXPOSE 8080
CMD ["node", "dist/server.js"]
```

Rules:
- Never end the final stage with `USER root`.
- Use numeric UID:GID in `USER`; symbolic names can resolve differently on host.
- `--chown=UID:GID` on `COPY --from=builder` avoids a separate `chown` layer.
- Do not mount writable host paths as root-owned directories into a non-root container.

### Minimal base images and image size

Smaller images have a smaller attack surface, transfer faster and start sooner.

| Strategy | Trade-off |
|---|---|
| `alpine` base | Very small; uses `musl libc`; some native modules need adjustment |
| `distroless` (Google) | No shell; smaller attack surface; harder to debug |
| `debian-slim` | Larger than alpine; `glibc`; easier compatibility with native modules |
| Scratch (Go binaries) | Minimal; requires static binary with no external libs |

Prefer `distroless` or `alpine` for new services. Use `debian-slim` only when native libraries require `glibc`.

Avoid:
- Installing debugging tools (`curl`, `vim`, `bash`) in the runtime image — add them in a separate debug build target only.
- Using `latest` tag for base images — pin to a specific digest or minor version: `node:22-alpine`.
- `ADD` with remote URLs — use `COPY` or a dedicated fetch stage.

Measure layer sizes: `docker image history <image>` shows each layer's size contribution.

### Image scanning

Scan every built image in CI before pushing to a registry.

**Trivy** (Aqua Security — widely used, open-source):

```bash
trivy image --exit-code 1 --severity CRITICAL,HIGH \
  --ignore-unfixed myapp:latest
```

- `--exit-code 1` fails the CI job on a match.
- `--severity CRITICAL,HIGH` focuses on actionable CVEs.
- `--ignore-unfixed` skips CVEs with no available fix (noise reduction).

Integrate in GitHub Actions:

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@a20de5420d57c4102486cdd9349b532415f2b8b7  # v0.26.0
  with:
    image-ref: myapp:${{ github.sha }}
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
    ignore-unfixed: true
```

Pin the action to a full SHA. Update the pin regularly (dependabot or renovate).

Treat CRITICAL CVEs with a fix as build-blocking. CRITICAL CVEs without a fix and HIGH CVEs: file a tracking issue, add a time-boxed `--ignore-unfixed` exception, do not ignore indefinitely.

## Examples

### Complete production Node.js Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

FROM node:22-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci
COPY . .
RUN npm run build && npm prune --production

FROM node:22-alpine AS runtime
ENV NODE_ENV=production PORT=8080
RUN addgroup -g 10001 -S appgroup \
 && adduser -u 10001 -S -G appgroup appuser
WORKDIR /app
COPY --from=builder --chown=10001:10001 /build/dist ./dist
COPY --from=builder --chown=10001:10001 /build/node_modules ./node_modules
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/healthz || exit 1
CMD ["node", "dist/server.js"]
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Single-stage Dockerfile with build tools in the runtime image | Ships compilers, test libraries and dev config to production; large image, big attack surface | Multi-stage build; copy only the built artefact to the runtime stage |
| `COPY . .` before installing dependencies | Any file change invalidates the dependency install cache layer | COPY manifests, run install, then `COPY . .` |
| Running as root in the final stage | Easier container escape if the process is compromised | Create a dedicated UID ≥ 10000; set `USER 10001:10001` |
| Using `latest` tag for the base image | Build is not reproducible; a base image update can silently introduce breaking changes or CVEs | Pin to `node:22-alpine` or a specific digest |
| No `.dockerignore` | Full source tree (including `.git` and `node_modules`) sent as build context; cache busted constantly | Add `.dockerignore` excluding `.git`, `node_modules`, `.env*`, `*.md` |
| Skipping image scanning in CI | CVEs ship to production unnoticed | Add `trivy image --exit-code 1 --severity CRITICAL,HIGH` in CI before push |

## Checklist

- [ ] `# syntax=docker/dockerfile:1` is the first line of every Dockerfile.
- [ ] Multi-stage build: build stage uses a full SDK; runtime stage uses a minimal base.
- [ ] `--mount=type=cache` used for package-manager caches.
- [ ] `COPY` manifest files before `COPY . .` to maximise cache reuse.
- [ ] Final stage ends with `USER <numeric-UID>:<numeric-GID>`; never `USER root`.
- [ ] Base image is pinned to a minor version tag, not `latest`.
- [ ] `.dockerignore` exists and excludes `.git`, secrets, local env files and dev artefacts.
- [ ] `trivy image --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed` runs in CI and passes.

## Verify with context7 and gh_grep

- **context7:** Resolve `docker/dockerfile` syntax version and the base image (e.g. `node:22-alpine`) to confirm current stable minor versions. Check: `--mount=type=cache` options (`sharing`, `target`, `id`), `HEALTHCHECK` instruction syntax.
- **gh_grep:** Search `--mount=type=cache` for real cache-mount patterns; `adduser -u 10001` for non-root user creation; `USER 10001` for numeric UID enforcement; `trivy-action` with `exit-code` for scanning wiring in CI.

## Sources

- Docker documentation — Dockerfile reference: https://docs.docker.com/reference/dockerfile/
- Docker documentation — Multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- BuildKit documentation: https://docs.docker.com/build/buildkit/
- Trivy documentation: https://trivy.dev/latest/docs/
