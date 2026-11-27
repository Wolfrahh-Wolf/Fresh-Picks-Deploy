# Hosting

Covers evaluating and configuring the four main hosting categories — static site CDN, container platform, platform-as-a-service (PaaS) and virtual machine — with provider-agnostic decision criteria and configuration essentials; checked 2026-11-26.

## Contents

- Choosing a hosting category
- Static site / CDN hosting
- Container hosting (managed container services)
- Platform-as-a-service (PaaS)
- Virtual machine (IaaS)
- Cross-cutting configuration rules

## Guidance

### Choosing a hosting category

Match the hosting type to the application's runtime model. Do not over-provision.

| Category | Best for | Trade-off |
|---|---|---|
| **Static CDN** | SPAs, pre-rendered sites, documentation, assets | Zero backend; no server runtime; dynamic data needs an API elsewhere |
| **Container platform** | Any Dockerised service with stateless workloads | More configuration; ideal for microservices, APIs, background workers |
| **PaaS** | Simple apps where the team does not want infra management | Less control; vendor lock-in; pricing scales with usage |
| **VM (IaaS)** | Workloads needing full OS control, specific kernel, or long-running processes | Full responsibility for patching, scaling, security |

Consult `docs/ARCHITECTURE.md` for the recorded hosting decision before proposing a change. Changes to hosting are covered by `AGENTS.md` Approval gates.

### Static site / CDN hosting

**Services:** Vercel, Netlify, Cloudflare Pages, AWS CloudFront + S3, GitHub Pages.

Configuration essentials:
- Set the **build command** and **publish directory** in the platform settings or a config file (e.g. `vercel.json`, `netlify.toml`).
- Configure **custom domains** with HTTPS. Platforms typically provision Let's Encrypt certs automatically.
- Set **cache headers** for static assets: `Cache-Control: public, max-age=31536000, immutable` for content-hashed filenames; `Cache-Control: no-cache` for `index.html` so stale shells are not served after a deploy.
- Configure **redirects and rewrites** so that client-side routes (e.g. `/dashboard`) are served the same `index.html` without 404s.
- Enable **HTTP security headers** via the platform's headers configuration: `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`.

Preview deployments (e.g. Vercel preview URLs for each PR) are useful for testing but must be protected from search engine indexing (`X-Robots-Tag: noindex`).

### Container hosting (managed container services)

**Services:** AWS ECS + Fargate, Google Cloud Run, Azure Container Apps, Fly.io, Railway (containers).

Configuration essentials:
- **Image pull**: always specify a digest or immutable tag in the task/service definition; never `latest`.
- **Resource requests and limits**: set CPU and memory limits; under-specification causes OOM kills, over-specification wastes cost.
- **Environment variables**: inject from the platform's secret store (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault) at runtime; never bake them into the image.
- **Health checks**: configure liveness and readiness probes pointing to `/healthz` and `/readyz`. Align probe intervals and timeouts with the values in the Compose file for parity.
- **Scaling**: set minimum replicas ≥ 2 for production to tolerate a node failure. Configure autoscaling on CPU or request count, not memory (memory is a trailing indicator).
- **Service mesh / networking**: services should communicate over private networks; only the ingress/load-balancer is public.

**Cloud Run specific:**
- Set `--concurrency` to match the app's thread model (Node.js: high; Python sync: low).
- Set `--min-instances 1` for latency-sensitive services to avoid cold starts.
- Use `--service-account` with the minimum IAM roles rather than the default compute service account.

### Platform-as-a-service (PaaS)

**Services:** Heroku, Render, Railway (PaaS mode), Fly.io Apps.

Configuration essentials:
- Use the platform's **config vars / environment** UI or CLI for secrets; never commit a `.env` file.
- Understand the **buildpack** or Dockerfile detection; ensure the production start command matches what the platform invokes (e.g. `Procfile` for Heroku).
- Set the **health check path** in the platform dashboard so the platform knows when a deployment is healthy before shifting traffic.
- Review **add-on databases**: managed database add-ons (Heroku Postgres, Render PostgreSQL) have connection limits; configure a connection pooler (PgBouncer) if the app opens many connections.
- Understand the **sleep/scaling behaviour**: free or hobby tiers spin down idle dynos; always use at least a standard tier for production.

### Virtual machine (IaaS)

**Services:** AWS EC2, GCP Compute Engine, Azure VMs, DigitalOcean Droplets.

Configuration essentials:
- Provision with **infrastructure as code** (Terraform, Pulumi, or cloud-specific CloudFormation); never manually configure production VMs via SSH.
- Use a **base AMI / image** that is patched, hardened and version-pinned; automate updates via an image-building pipeline (Packer or similar).
- Run the application inside Docker on the VM; manage it with Compose or systemd for simpler setups, or migrate to a container platform.
- Configure the **firewall / security group** to allow only the ports needed: typically 443 inbound from the internet, all other ports internal only.
- Enable **automatic OS patching** (AWS Systems Manager Patch Manager, GCP OS Config, `unattended-upgrades` on Debian) with a scheduled maintenance window.
- Assign the VM a **dedicated IAM role** (not an access key) to access cloud services.

For infrastructure security, load `security-engineering`.

### Cross-cutting configuration rules

These apply to every hosting category:

- **HTTPS everywhere**: reject plain HTTP at the platform edge; redirect 301 to HTTPS. Configure HSTS with `includeSubDomains` and a `max-age` ≥ 1 year.
- **Environment variable naming**: match names exactly between all environments (`DATABASE_URL`, not `DB_URL` in staging vs. `DATABASE_URL` in production).
- **Domain strategy**: use subdomains for environments (`staging.example.com`, `api.example.com`); avoid path-based environment switching unless forced by the platform.
- **Observability hook**: every hosted service must ship structured logs and expose `/healthz` before going live (see `monitoring.md`).
- **Cost controls**: set billing alerts on the cloud provider account for unexpected spend spikes (a runaway autoscaling event or a leaked credential).

## Examples

### Minimal `vercel.json` for a React SPA

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains" }
      ]
    }
  ]
}
```

### Cloud Run deploy command (with OIDC in CI)

```bash
# Requires OIDC-acquired credentials; never hardcode --service-account key
gcloud run deploy my-api \
  --image gcr.io/my-project/my-api@sha256:<digest> \
  --region us-central1 \
  --service-account my-api-sa@my-project.iam.gserviceaccount.com \
  --set-secrets DATABASE_URL=projects/my-project/secrets/db-url:latest \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --port 8080 \
  --no-allow-unauthenticated
```

> ⚠️ This command deploys to a live environment. Run only after user approval per `AGENTS.md` Approval gates.

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Deploying `latest` image tag to production | Tag is mutable; re-deploy can silently change the running code | Pin to a digest or immutable content-addressed tag |
| Baking secrets into the container image | Secrets exposed via `docker history`; image registry breach leaks credentials | Inject at runtime from the platform's secret store |
| Serving `index.html` with long `max-age` cache | Users receive stale app shells after a deploy | Set `Cache-Control: no-cache` for `index.html`; use content-hashing for assets |
| Not setting memory limits on containers | A memory leak causes OOM kill and pod eviction without a trace | Always set memory requests and limits; alert on memory usage > 80% |
| Manually SSH-ing into a production VM to apply changes | Changes are undocumented, unrepeatable and invisible to the team | Make all changes via IaC or the CI pipeline; SSH only for emergency read-only diagnosis |

## Checklist

- [ ] Hosting category matches the application's runtime model; decision recorded in `docs/ARCHITECTURE.md`.
- [ ] HTTPS enforced at the edge; HSTS header set with `max-age ≥ 31536000`.
- [ ] Secrets injected at runtime from the platform's secret store; none in the image or repository.
- [ ] Image tag pinned to a digest or immutable tag; `latest` is not used.
- [ ] Health check path (`/healthz`) configured in the platform.
- [ ] Minimum replicas ≥ 2 for production container workloads.
- [ ] Billing alert configured on the cloud account.

## Verify with context7 and gh_grep

- **context7:** For platform-specific CLI tools (`vercel`, `gcloud`, `fly`, `heroku`), resolve the CLI version in the CI environment and check current command syntax and flags. Check: `gcloud run deploy` flags (`--set-secrets`, `--min-instances`), `vercel.json` schema, `fly.toml` service configuration.
- **gh_grep:** Search `vercel.json` with `rewrites` for SPA routing patterns; `gcloud run deploy` with `--set-secrets` for secret injection; `Cache-Control: no-cache` applied to `index.html` in deployment scripts.

## Sources

- Vercel configuration reference: https://vercel.com/docs/projects/project-configuration
- Netlify configuration reference: https://docs.netlify.com/configure-builds/file-based-configuration/
- Google Cloud Run documentation: https://cloud.google.com/run/docs
- AWS ECS task definition reference: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html
