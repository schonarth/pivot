---
name: Global In-Memory Query Observability
description: Process-local request query stats for detecting heavy ORM access without exposing user data
type: reference
---

# ADR-008: Global In-Memory Query Observability Over User-Scoped Reporting

Status: Accepted
Date: 2026-04-24
SPEC: None

## Context

The API can hide N+1 and query-heavy request patterns until ordinary development traffic happens to exercise larger portfolios, watchlists, or timelines. Without request-level observability at the ORM boundary, these issues are found late and usually require ad hoc debugging.

## Decision

Add a Django ORM query detector that records bounded, process-local, global request stats and exposes them through an authenticated system endpoint. Reports will include request metadata, query counts, timing, and normalized SQL fingerprints, but never request bodies, SQL parameters, response bodies, or per-user stat partitions.

## Consequences

- Developers can inspect query-heavy requests during normal work without enabling a profiler or changing end-user responses
- Global stats fit the operational problem: N+1 risk belongs to endpoints and code paths, not individual users
- In-memory storage avoids migrations, retention policy, and persistence of potentially sensitive operational traces
- Process-local stats are intentionally incomplete across multiple workers; they are a lightweight development signal, not durable monitoring
- Normalized SQL fingerprints are acceptable to expose to authenticated users because the codebase is open source and values are stripped
- AGENTS.md should include a short reminder to check this endpoint for N+1 signals at the end of large implementation tasks or test runs, before stopping the server
