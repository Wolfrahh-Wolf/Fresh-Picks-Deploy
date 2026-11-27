# GraphQL API Design

Covers schema design, resolver patterns, N+1 mitigation with DataLoader, Relay cursor pagination, error handling, query cost limits and schema evolution; based on the GraphQL June 2018 specification and Relay cursor connection spec, checked 2026-11-26.

## Contents

- Schema design principles
- Resolvers and the N+1 problem
- Pagination with Relay cursor connections
- Errors and partial data
- Query cost and depth limits
- Schema evolution and deprecation

## Guidance

### Schema design principles

- Model the graph, not the database. Types represent domain concepts; fields represent relationships.
- Use specific scalar types (`ID`, `Int`, `Float`, `String`, `Boolean`) and add custom scalars (`DateTime`, `URL`, `JSON`) only when the base types are insufficient. Document custom scalars.
- Name queries as nouns (`user`, `orders`), mutations as verb-object pairs (`createOrder`, `cancelOrder`), subscriptions as past-tense events (`orderStatusChanged`).
- Keep field names camelCase; type names PascalCase.
- Prefer non-null (`!`) only when the field is guaranteed to be present on every occurrence. Over-using non-null makes schema evolution harder.
- Never expose internal database IDs directly as the `id` field without opaque encoding; use a global ID pattern (`base64("TypeName:rawId")`).

### Resolvers and the N+1 problem

A naive resolver that fetches related records one at a time causes N+1 database queries: one for the parent list, then one per row for the child.

**Rule:** Never call the database or a downstream service inside a resolver for a list field without batching.

**DataLoader pattern** (the standard solution):

- Create one DataLoader per data source per request (never share loaders across requests; the per-request cache is not thread-safe).
- Each DataLoader accepts an array of keys and returns a matching array of values (or errors).
- Resolvers call `loader.load(key)` and return the promise; DataLoader batches all `load` calls within the same event-loop tick into a single batch function call.
- The batch function should use `IN (...)` queries or batch RPCs, not loops.

```javascript
// Instantiate per request, e.g. in Apollo Server context
import DataLoader from 'dataloader';

function createLoaders(db) {
  return {
    userById: new DataLoader(async (ids) => {
      const rows = await db.query(
        'SELECT * FROM users WHERE id = ANY($1)', [ids]
      );
      // Return rows in the same order as ids
      const map = Object.fromEntries(rows.map(r => [r.id, r]));
      return ids.map(id => map[id] ?? new Error(`User ${id} not found`));
    }),
  };
}
```

Add loaders to the GraphQL context so every resolver in the request shares the same batch.

### Pagination with Relay cursor connections

Use Relay cursor-based connections for every list field that can grow beyond a handful of items.

Connection structure:

```graphql
type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
}

type OrderEdge {
  cursor: String!
  node: Order!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

Arguments on the connection field: `first: Int`, `after: String`, `last: Int`, `before: String`. Implement at minimum `first` and `after` for forward pagination.

- Cursors are opaque to the client (base-64 encoded position or timestamp).
- Never expose raw offsets as cursors; they break under concurrent inserts.
- Apply a default and maximum for `first`/`last` server-side (e.g. default 20, max 100).

### Errors and partial data

GraphQL returns HTTP 200 for all responses, including those with errors. Errors appear in the top-level `errors` array; partial successful data appears in `data`. Do not use HTTP 4xx/5xx for field-level GraphQL errors.

Error format per spec:

```json
{
  "data": { "user": null },
  "errors": [
    {
      "message": "User not found",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["user"],
      "extensions": { "code": "NOT_FOUND", "traceId": "abc-123" }
    }
  ]
}
```

- Use `extensions.code` for machine-readable error classification (`NOT_FOUND`, `FORBIDDEN`, `VALIDATION_ERROR`, `INTERNAL`).
- Never expose stack traces or internal error messages in `message`.
- For authentication failures, still return HTTP 401; for wholesale server crashes, return HTTP 500. Reserve HTTP 200 for responses that contain a valid GraphQL response envelope.
- Design nullable fields defensively: if a field's resolver can fail without invalidating the rest of the query, make it nullable so partial data is returned.

### Query cost and depth limits

Clients can craft deeply nested or large-argument queries that overload resolvers even with DataLoader.

Apply both limits on every server:

**Depth limit:** Reject queries deeper than a configured threshold (typically 7–10 levels). Calculate depth before execution.

**Cost limit:** Assign a cost weight to each field (1 for scalars, configurable for connections). Multiply by pagination arguments (`first`). Reject queries whose total cost exceeds a budget (e.g. 1 000 units) before execution.

```javascript
// Example using graphql-query-complexity
import { getComplexity, simpleEstimator, fieldExtensionsEstimator } from 'graphql-query-complexity';

const complexity = getComplexity({
  schema,
  query: document,
  variables,
  estimators: [
    fieldExtensionsEstimator(),
    simpleEstimator({ defaultComplexity: 1 }),
  ],
});

if (complexity > MAX_COMPLEXITY) {
  throw new Error(`Query complexity ${complexity} exceeds limit ${MAX_COMPLEXITY}`);
}
```

Also consider persisted queries (Automatic Persisted Queries, APQ): clients send a hash; the server executes only pre-registered hashes in production, eliminating ad-hoc query abuse.

### Schema evolution and deprecation

GraphQL schemas must evolve without breaking existing clients. The default rule is **additive-only**.

- Add new fields and types freely; they are non-breaking.
- Mark deprecated fields with `@deprecated(reason: "Use newField instead.")`.
- Never remove a field or change its type until every consumer has migrated and the deprecation has been communicated with a sunset date.
- Use schema changelogs or automated tools (e.g. `graphql-inspector`) to detect breaking changes in CI.
- Avoid nullable-to-non-null changes (`String` → `String!`); they are breaking because clients may conditionally handle null.
- Adding new required arguments (without a default) is a breaking change; prefer optional arguments with defaults.

## Examples

### Full resolver with DataLoader (TypeScript, Apollo Server 4)

```typescript
// context.ts
import DataLoader from 'dataloader';
import { db } from './db';

export type Context = { loaders: ReturnType<typeof createLoaders> };

export function createLoaders() {
  return {
    productById: new DataLoader<string, Product | null>(async (ids) => {
      const rows = await db.products.findMany({ where: { id: { in: [...ids] } } });
      const map = new Map(rows.map(r => [r.id, r]));
      return ids.map(id => map.get(id) ?? null);
    }),
  };
}

// resolvers.ts
export const orderResolvers = {
  Order: {
    product: (order: Order, _args: unknown, ctx: Context) =>
      ctx.loaders.productById.load(order.productId),
  },
};
```

### Schema excerpt with connection and deprecation

```graphql
type Query {
  orders(first: Int = 20, after: String): OrderConnection!
  # @deprecated: use `orders` with filter argument
  pendingOrders: [Order!]! @deprecated(reason: "Use orders(filter: { status: PENDING })")
}
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Calling the DB directly inside a list resolver without DataLoader | N+1 queries; a list of 100 items triggers 101 DB calls | Use DataLoader; batch all keys in one query |
| Returning `[Order!]!` without pagination | Client receives unbounded data; large lists OOM the server | Use Relay cursor connection with `first`/`after` and enforce a max |
| Re-using a DataLoader instance across requests | Stale cached data served to different users | Instantiate DataLoader inside the request context factory |
| Removing a deprecated field without a sunset period | Existing clients break silently | Give at least one release cycle notice; use `graphql-inspector` in CI |
| Not setting depth or cost limits | A client crafts a deeply nested query and exhausts server resources | Apply depth and cost limits before query execution |
| Using HTTP 4xx for field-level GraphQL errors | Clients that check HTTP status discard the partial `data` payload | Use HTTP 200 with the `errors` array; reserve HTTP 4xx for transport-level failures |

## Checklist

- [ ] Every list field uses a Relay cursor connection (or is bounded and tiny).
- [ ] Every related-object field resolver uses DataLoader (no per-row DB calls).
- [ ] DataLoader instances are created per request, not per schema.
- [ ] Query depth and cost limits are configured and enforced before execution.
- [ ] Deprecated fields carry a `@deprecated(reason: ...)` directive.
- [ ] `extensions.code` is set on all errors; stack traces are absent.
- [ ] APQ or persisted queries are enabled on public-facing endpoints.
- [ ] `graphql-inspector` or equivalent diff runs in CI to catch breaking changes.

## Verify with context7 and gh_grep

- **context7:** Resolve `dataloader`, `graphql-js`, `@apollo/server` and `graphql-query-complexity` at the version in `package.json`. Check: DataLoader constructor options (caching, batch scheduling), Apollo Server 4 `contextValue` factory signature, complexity estimator configuration.
- **gh_grep:** Search `new DataLoader` for real batch-function patterns; `fieldExtensionsEstimator` or `simpleEstimator` for cost-limit wiring; `hasNextPage` with `endCursor` for connection implementation; `@deprecated` with `reason:` for schema evolution examples.

## Sources

- GraphQL Specification (June 2018 edition): https://spec.graphql.org/June2018/
- Relay Cursor Connections Specification: https://relay.dev/graphql/connections.htm
- DataLoader (GitHub): https://github.com/graphql/dataloader
- graphql-query-complexity (GitHub): https://github.com/slicknode/graphql-query-complexity
