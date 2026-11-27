# Rollback

Covers rollback strategies for containers and databases, decision triggers, the expand-and-contract migration pattern, rollback rehearsal and post-rollback verification; checked 2026-11-26.

## Contents

- Rollback strategies
- Database migration considerations
- Rollback decision triggers
- Rehearsal and runbook
- Post-rollback verification

## Guidance

### Rollback strategies

Choose the strategy when designing the deployment, not during an incident.

#### Immediate image rollback (stateless services)

Redeploy the previous container image. This is the fastest and least risky option when no backwards-incompatible database migration has run.

```bash
# Docker Compose: change the image tag in compose.yaml and redeploy
docker compose pull && docker compose up -d

# Cloud Run
gcloud run services update-traffic my-api \
  --to-revisions PREV_REVISION=100 --region us-central1

# Kubernetes
kubectl rollout undo deployment/my-api
```

> ⚠️ All of these touch a live environment. Run only after user approval.

#### Blue-green cutover

Two identical environments (blue = live, green = new). Traffic is switched at the load balancer or DNS level.

Rollback: flip traffic back to blue. The old environment is preserved until the new one is verified stable.

Considerations:
- Requires double the infrastructure during the cutover window.
- Both environments share the same database; the schema must be compatible with both versions simultaneously (see database migration considerations below).
- DNS-level switching has propagation delay; prefer load-balancer-level switching for instant rollback.

#### Canary rollback

New version receives a small traffic percentage; metrics determine whether to progress or abort.

If metrics breach thresholds (error rate, latency SLO), redirect all traffic back to the previous version. Tools like Argo Rollouts or Flagger automate this analysis.

#### Feature-flag rollback

A deployed container hosts the new code, but the feature is off by default. Rolling back = toggling the flag off, with zero infrastructure change.

This decouples deployment from release. Use feature flags for risky user-facing changes; it eliminates the need for most code rollbacks.

### Database migration considerations

A container rollback fails silently if the previous image expects a database schema that the current migration has already removed or changed. Database migrations and application rollbacks must be planned together.

**Expand-and-contract pattern** (the only safe approach for zero-downtime rollbacks):

| Phase | Action | Safety |
|---|---|---|
| **Expand** | Add new column/table as nullable; write to both old and new column | Both old and new app versions work |
| **Migrate** | Backfill old data to the new column; switch reads to new column | Old app reads old column; new app reads new column |
| **Verify** | Confirm new version is stable for ≥ 1 release cycle | Rollback window open |
| **Contract** | Remove old column/table in a separate, later release | Old column gone; rollback to old version would break — but the old version is now ≥ 1 release behind |

**Rules:**
- Never combine a breaking schema change (drop column, rename column) with application code that removes support for the old schema in the same release.
- Never run Phase 3 (contract) in the same deployment as Phase 1.
- If a migration has already run before the rollback is triggered, assess whether the old image is still compatible. If not, the rollback must include a reverse migration (down migration).
- Always test the down migration (rollback script) in staging before running in production.

**Down migrations:**

Maintain a reversible down migration for every up migration where rollback is possible:

```sql
-- up: add nullable column (expand)
ALTER TABLE orders ADD COLUMN external_id TEXT;

-- down: reverse if rollback needed before contract phase
ALTER TABLE orders DROP COLUMN external_id;
```

After Phase 3 (contract), the down migration for the original expand can be removed — there is no longer a previous version that relies on the old schema.

### Rollback decision triggers

Define triggers before each deployment, not during an incident.

**Automatic triggers** (configure in monitoring/alerting):
- HTTP 5xx error rate exceeds baseline by more than X% for more than Y minutes (e.g. > 2% for > 5 minutes).
- p99 latency exceeds SLO threshold.
- `/readyz` health check fails on the new version for more than 3 consecutive checks.

**Manual triggers** (notify the team and rollback):
- A critical bug is reported that the new version introduced.
- A security vulnerability is discovered in the deployed code.
- A deployment smoke test fails.

Write down the specific thresholds in `docs/MEMORY.md` as a durable constraint.

### Rehearsal and runbook

A rollback that has never been rehearsed is a rollback that will fail during an incident.

**Minimum rehearsal requirements:**
- Run the rollback procedure in staging once before every significant production deployment.
- Confirm the previous image still exists in the registry (do not let old images expire before the rollback window closes — keep at least 2 previous releases in the registry).
- Confirm the down migration runs cleanly in staging.
- Time the full rollback process; it must complete within the team's recovery time objective (RTO).

**Rollback runbook template** (store in `docs/runbooks/rollback.md` or inline in the task file):

```markdown
## Rollback Runbook for [service] [version]

Trigger: [specific alert or symptom]
Decision maker: [on-call engineer or team lead]
Approval required: yes (per AGENTS.md)

### Steps
1. Notify #incidents channel: "Starting rollback of [service] from [new] to [prev]."
2. [Platform-specific rollback command]
3. Verify /healthz returns 200.
4. Verify error rate returns to baseline in monitoring.
5. If database migration ran: execute down migration [path/to/down.sql].
6. Confirm smoke test passes.
7. Update docs/MEMORY.md with the incident trigger and resolution.

### Rollback duration estimate: [X minutes]
### RTO: [Y minutes]
```

### Post-rollback verification

After executing the rollback:

1. Confirm `/healthz` and `/readyz` return 200.
2. Check the error rate in monitoring; confirm it returns to the pre-deployment baseline.
3. Run the deployment smoke test suite against the rolled-back environment.
4. Check that no new errors appeared in logs during or after the rollback.
5. If a down migration ran, spot-check that the data is in the expected state.
6. Record the incident: trigger, timeline, resolution and root cause in `docs/MEMORY.md`.
7. Open a follow-up task to fix the root cause before the next release attempt.

## Examples

### Cloud Run traffic split during rollback

```bash
# Identify the previous stable revision
gcloud run revisions list --service my-api --region us-central1

# Shift all traffic back to the previous revision
gcloud run services update-traffic my-api \
  --to-revisions my-api-00042-abc=100 \
  --region us-central1
```

> ⚠️ Requires user approval; this is a live production change.

### Kubernetes rollback and verification

```bash
# Check rollout history
kubectl rollout history deployment/my-api

# Roll back to the previous revision
kubectl rollout undo deployment/my-api

# Wait for rollback to complete
kubectl rollout status deployment/my-api --timeout=5m

# Confirm pods are running
kubectl get pods -l app=my-api
```

### Down migration example (Flyway-style naming)

```
db/migrations/
  V20261126__add_external_id.sql      ← up migration
  U20261126__add_external_id.sql      ← undo / down migration
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Combining a breaking schema change and removing old code in one release | The previous image breaks immediately against the new schema; rollback is impossible | Use expand-and-contract across separate releases |
| Never rehearsing the rollback | A rehearsal-free rollback in production panics the team and takes 10× longer | Rehearse in staging before every significant deployment |
| Letting old images expire from the registry | The previous version is no longer pullable; rollback requires a rebuild | Retain at least 2 previous releases in the registry with an explicit retention policy |
| Rolling back only the application, not the migration | Old application code tries to read a column that the migration renamed or dropped | Assess migration compatibility before rollback; run down migration if needed |
| No decision thresholds defined before deploy | Rollback decision is made emotionally during an incident | Define specific triggers (error rate %, latency SLO) in advance and document them |

## Checklist

- [ ] Rollback runbook exists and specifies the exact command for the platform.
- [ ] Rollback rehearsed in staging within the last sprint or before this deployment.
- [ ] Previous container image retained in the registry (at least 2 releases back).
- [ ] All database migrations are backwards-compatible with the previous release.
- [ ] Down migration written and tested for every up migration.
- [ ] Rollback decision thresholds (error rate, latency) defined and recorded before deploy.
- [ ] Post-rollback verification steps completed and recorded.
- [ ] Incident cause documented in `docs/MEMORY.md`.

## Verify with context7 and gh_grep

- **context7:** Not required for rollback strategy decisions. For platform-specific CLI commands (`gcloud run`, `kubectl rollout undo`), resolve the CLI version and check command flags.
- **gh_grep:** Search `kubectl rollout undo` for real rollback patterns; `update-traffic` with `gcloud run` for Cloud Run traffic management; `V[0-9]*__` with `U[0-9]*__` for paired up/undo migration naming conventions.

## Sources

- Google Cloud Run — Traffic management: https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration
- Kubernetes — Rollout undo: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment
- Expand-and-contract pattern: https://martinfowler.com/bliki/ParallelChange.html
