# MongoDB

Covers MongoDB 8.0 document modelling, embedding versus referencing, schema validation, aggregation pipelines and consistency settings; checked against MongoDB 8.0 official documentation on 2026-11-26. The project's driver manifest and server version determine which features are available.

## Contents

- Document modelling principles
- Embedding versus referencing
- Schema validation with `$jsonSchema`
- Aggregation pipelines
- Consistency settings (`readConcern`, `writeConcern`, `readPreference`)
- Indexes and operational guardrails

## Guidance

### Document modelling principles

Model documents around **query and update access patterns**, not entity normalisation alone. Data read and updated together belongs in the same document; data that grows without bound or updates independently belongs in separate documents.

**Hard structural limits to design around:**
- **16 MiB maximum BSON document size** — never store unbounded arrays (logs, comments, event streams) inside a single document.
- **Document growth and WiredTiger rewrites** — appending heavily to large embedded arrays forces full-document rewrites; split or bucket high-churn child arrays.
- **No cross-collection foreign key constraints** — referential integrity between collections is enforced by application logic or transactions, not by the engine.

Apply standard MongoDB modelling patterns only when access patterns justify them:
- **Subset pattern:** Embed the most recent N items (for example, last 10 reviews) on the parent document and store the full history in a separate collection.
- **Bucket pattern:** Group high-frequency time-series or telemetry points into fixed-size buckets (or use a native Time Series collection) instead of one document per point.
- **Computed pattern:** Maintain pre-aggregated counts or totals on the parent document and update them atomically with `$inc` inside the same write or transaction. Document the invariant in `docs/DB.md`.

### Embedding versus referencing

| Criterion | Embed (subdocument / array) | Reference (`_id` link across collections) |
|---|---|---|
| Cardinality | 1:1 or bounded 1:few (tens to low hundreds) | Bounded 1:many, unbounded 1:many, or many:many |
| Read pattern | Child always read with parent | Parent and child frequently queried independently |
| Write pattern | Child edited with parent | Child updated frequently without touching parent |
| Document size risk | Remains well under 16 MiB | Child growth would risk 16 MiB or large rewrites |
| Consistency need | Atomic single-document write guarantees consistency | Requires multi-document transaction if cross-document atomicity is required |

Single-document writes in MongoDB are always atomic across all embedded subdocuments and arrays. Prefer embedding when cardinality is strictly bounded and data is read together; reference when arrays are unbounded, shared across parents, or independently updated.

### Schema validation with `$jsonSchema`

Enforce structural invariants in the database with `$jsonSchema` rather than relying solely on application DTOs or ODMs.

- Apply `validationLevel: "strict"` and `validationAction: "error"` for new collections; use `"moderate"` / `"warn"` temporarily when backfilling legacy collections before tightening to `"error"`.
- Always specify `bsonType` (`"object"`, `"string"`, `"int"`, `"long"`, `"decimal"`, `"date"`, `"bool"`) rather than JSON `type` when integer/decimal precision matters. Use `bsonType: "decimal"` (`Decimal128`) for monetary amounts, never `"double"`.
- Remember `additionalProperties: false` requires listing `_id` explicitly in `properties`.

### Aggregation pipelines

Order pipeline stages to reduce document volume and memory footprint early:

1. **`$match` first:** Filter as early as possible so MongoDB uses collection indexes instead of scanning every document.
2. **`$sort` early (right after `$match`):** Allows the planner to satisfy sorting from an index rather than an in-memory sort (100 MiB stage memory limit before spilling to disk).
3. **`$project` or `$unset` before expensive stages:** Drop unused large fields before `$unwind`, `$group`, or `$lookup`.
4. **`$lookup` carefully:** Always index the foreign collection's `foreignField`. In MongoDB 8.0, `$lookup` is supported inside multi-document transactions (except specialised forms such as `$graphLookup` on sharded collections). Prefer `$lookup` with a pipeline when only a filtered subset of foreign fields is needed.
5. **Express Path (MongoDB 8.0):** Simple equality/point queries with single-field indexes bypass full query-planning overhead automatically; keep hot-path lookups simple rather than wrapping trivial reads in multi-stage aggregations.

### Consistency settings (`readConcern`, `writeConcern`, `readPreference`)

Configure concerns explicitly on critical operations rather than trusting driver defaults blindly.

| Setting | Option | Guarantee | When to use |
|---|---|---|---|
| `writeConcern` | `{ w: "majority", j: true }` | Acknowledged by a majority of voting replica set nodes and flushed to the on-disk journal | Financial writes, state transitions, orders, audit records (required for failover durability) |
| `writeConcern` | `{ w: "majority" }` (8.0 default) | Replicated to majority memory; survives primary step-down unless simultaneous power loss hits nodes before journal flush | Standard durable application writes |
| `writeConcern` | `{ w: 1 }` | Acknowledged only by primary memory; can roll back on primary failover | Ephemeral telemetry or regenerable cache-like records only |
| `readConcern` | `"majority"` | Reads only majority-committed data; never sees data that could roll back | Billing, auth state, compliance reads |
| `readConcern` | `"local"` (default) | Reads node's latest data; fast, but uncommitted-to-majority writes could roll back on primary crash | Non-critical reads where slight rollback risk is acceptable |
| `readConcern` | `"linearizable"` | Reads majority-committed data current as of request start on primary | Single-document read-after-write guarantees without a transaction |
| `readConcern` | `"snapshot"` | Consistent point-in-time view across operations | Multi-document transactions |

**`readPreference`:** Default to `"primary"` for consistent reads. Use `"secondaryPreferred"` only for read-heavy analytics or non-critical dashboards where replication lag (stale reads) is explicitly acceptable. Use causally consistent sessions (`ClientSession` with `causalConsistency: true`) when a caller must read its own writes across operations.

Always set `wtimeoutMS` (for example, `5000`) on critical writes or `maxTimeMS` on queries/aggregations so a partitioned replica set or runaway pipeline fails fast instead of exhausting connection pools. In MongoDB 8.0, clusters can enforce a default read timeout (`defaultMaxTimeMS`) and persistent query settings (`setQuerySettings`) across restarts.

### Indexes and operational guardrails

Follow the **ESR (Equality, Sort, Range)** rule when ordering compound index keys:

1. Fields matched with exact equality (`=`, `$in` with small lists) first.
2. Fields used in `sort()` next (matching sort direction).
3. Fields matched with range operators (`$gt`, `$lt`, `$gte`, `$lte`, `$ne`) last.

Create indexes on all `foreignField` targets used by `$lookup`, and avoid indexing huge, rapidly changing arrays (multikey index write amplification). Keep `totalIndexSize` comfortably within RAM (WiredTiger cache) for hot working sets.

## Examples

### Bounded embedding vs referencing with `$jsonSchema`

```javascript
// Bad: unbounded comments array embedded in post (will eventually hit 16 MiB)
// { _id: ObjectId("..."), title: "...", comments: [ { authorId, body, createdAt }, ... ] }

// Good: keep bounded summary count on parent, store comments in their own collection
db.createCollection("comments", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["postId", "authorId", "body", "createdAt"],
      additionalProperties: false,
      properties: {
        _id: { bsonType: "objectId" },
        postId: { bsonType: "objectId" },
        authorId: { bsonType: "objectId" },
        body: { bsonType: "string", minLength: 1, maxLength: 10000 },
        createdAt: { bsonType: "date" }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
});

// ESR-aligned index for paginated comments per post
db.comments.createIndex({ postId: 1, createdAt: -1 });
```

### Aggregation pipeline and majority write concern

```javascript
// Bad: $lookup before $match scans the whole orders collection
db.orders.aggregate([
  { $lookup: { from: "customers", localField: "customerId", foreignField: "_id", as: "customer" } },
  { $match: { status: "paid", total: { $gte: NumberDecimal("100.00") } } }
]);

// Good: filter and project first, then join; enforce maxTimeMS
db.orders.aggregate([
  { $match: { status: "paid", total: { $gte: NumberDecimal("100.00") } } },
  { $sort: { createdAt: -1 } },
  { $limit: 50 },
  { $project: { customerId: 1, total: 1, createdAt: 1 } },
  {
    $lookup: {
      from: "customers",
      localField: "customerId",
      foreignField: "_id",
      pipeline: [{ $project: { name: 1, tier: 1 } }],
      as: "customer"
    }
  }
], { maxTimeMS: 2000, readConcern: { level: "majority" } });

// Critical state change with durable writeConcern
await db.collection("orders").updateOne(
  { _id: orderId, status: "pending" },
  { $set: { status: "paid", paidAt: new Date() } },
  { writeConcern: { w: "majority", j: true, wtimeoutMS: 5000 } }
);
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Embedding unbounded arrays | Exceeds 16 MiB BSON limit and causes expensive document rewrites | Reference in a child collection or use the subset/bucket pattern |
| Using `double` for currency | Binary floating-point rounding corrupts monetary totals | Use `Decimal128` (`NumberDecimal` / `bsonType: "decimal"`) |
| Placing `$lookup` before `$match` | Joins every row in the collection before filtering | Place `$match`, `$sort` and `$limit` as early as possible |
| Missing index on `$lookup` `foreignField` | Triggers a full collection scan on the foreign collection per input document | Create an index on `foreignField` before running the pipeline |
| Using `w: 1` for critical writes | Primary crash before replication silently loses acknowledged writes | Use `{ w: "majority", j: true }` |
| Reading from secondaries for read-after-write flows | Replication lag serves stale data | Read from `"primary"` or use causally consistent sessions |
| Omitting `maxTimeMS` on user-triggered aggregations | Runaway queries saturate CPU and WiredTiger tickets | Set explicit `maxTimeMS` per query or configure cluster `defaultMaxTimeMS` |

## Checklist

- [ ] No embedded array can grow without bound toward the 16 MiB BSON document limit.
- [ ] Monetary values use `Decimal128` (`bsonType: "decimal"`), never `double`.
- [ ] Collections enforce invariants via `$jsonSchema` validation with `validationAction: "error"`.
- [ ] Aggregation pipelines place `$match` and `$sort` before `$lookup`, `$unwind`, and `$group`.
- [ ] Every `$lookup` `foreignField` has a supporting index.
- [ ] Compound indexes follow Equality, Sort, Range (ESR) key order.
- [ ] Critical writes set `writeConcern: { w: "majority", j: true }` with `wtimeoutMS`.
- [ ] Reads requiring rollback safety use `readConcern: "majority"` (or `"snapshot"` in transactions).
- [ ] Queries and aggregations carry `maxTimeMS` bounds.
- [ ] Document models and deliberate denormalisation invariants are recorded in `docs/DB.md`.

## Verify with context7 and gh_grep

- **context7:** Verify the exact Node.js (`mongodb` package) or Python (`pymongo`) driver version from the manifest (`package.json`, `pyproject.toml`) for option names (`wtimeoutMS` vs `wtimeout`, `ClientSession` transaction APIs). Queries: `mongodb 8.0 lookup transactions`, `mongodb driver writeConcern majority journal`, `mongodb createCollection jsonSchema validator`.
- **gh_grep:** Search `writeConcern` and `readConcern` in the codebase to confirm critical paths use `"majority"` and `j: true`; search `.aggregate([` to check `$match` placement and `maxTimeMS` usage.

## Sources

- MongoDB Manual — Data Modeling: https://www.mongodb.com/docs/manual/data-modeling/
- MongoDB Manual — Aggregation: https://www.mongodb.com/docs/manual/aggregation/
- MongoDB Manual — Read Concern: https://www.mongodb.com/docs/manual/reference/read-concern/
- MongoDB Manual — Write Concern: https://www.mongodb.com/docs/manual/reference/write-concern/
- MongoDB Manual — Schema Validation & Transactions: https://www.mongodb.com/docs/manual/
