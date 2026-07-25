# 06 - MCP Evidence Review and Correction Parity

## Purpose

Expose the same authenticated evidence-review and correction operations to delegated MCP assistants, with strict operator scope and assistant audit identity.

## Roadmap Milestone

Milestone 09 - Fact Corrections and Conflict Detection

## Governing SPEC

SPEC-009 Fact Corrections and Conflict Detection

## Status

done

## Owner

Codex / implementation

## Date Started

2026-07-25

## Date Completed

2026-07-25

## Branch

feat/autonomous/09-fact-corrections

## Dependencies

- `00 - milestone coordination.md`
- `03 - correction-review-and-treatment-contracts.md`
- `04 - recommendation-invalidation-and-evidence-api.md`

## Likely Files Touched

- `backend/mcp/auth.py`
- `backend/mcp/views.py`
- `backend/mcp/serializers.py`
- `backend/mcp/urls.py`
- `backend/mcp/test_views.py`
- `backend/ai/services.py`
- `backend/ai/test_*.py`
- `docs/reference/*`

## Detailed Requirements

- let an authenticated assistant retrieve evidence, correction history, treatment, invalidation state, and its operator's completed fact-key suggestions
- let it create or supersede fact corrections, artifact review states, and source stances within the authenticated operator scope
- route MCP mutations through the same backend service as UI mutations
- capture immutable `original_value` only from the referenced platform artifact; reject MCP-supplied or altered values
- retain acting assistant identity in `created_by`/audit history
- guide clients to reuse an existing suitable fact key while permitting a new key
- publish the operations in MCP schema/reference documentation
- do not provide automatic conflict queues or autonomous record changes

## Validation Scenarios

- assistant can only read/write its authorized operator's records
- audit history distinguishes UI operator actions from delegated assistant actions
- MCP and UI produce the same treatment/invalidation outcome for equivalent mutation
- MCP cannot forge `original_value` or cross-reference an unauthorized artifact
- schema advertises only the bounded evidence-review operations

## Task Steps

1. Reuse existing MCP authentication and the shared correction service; do not duplicate business rules in views.
2. Define minimal request/response serializers that expose structured records and fact-key suggestions.
3. Add retrieval and mutation endpoints plus schema entries.
4. Add scope, audit, immutable-value, and parity tests.
5. Update API reference documentation.

## Tests to Add or Update

- MCP authenticated retrieval and mutation tests
- cross-operator authorization tests
- assistant-audit-identity tests
- UI/MCP service parity tests
- original-value forgery rejection tests

## Commands to Run

- `cd backend && pytest mcp/test_views.py ai/test_strategy_validation.py ai/test_views.py`
- `cd backend && ruff check mcp ai`

## Exit Conditions

- MCP supports equivalent bounded evidence-review operations
- scope, audit identity, and immutable original-value rules are enforced
- no MCP-specific treatment logic or autonomous queue is introduced
- documentation matches the implemented contract

## Implementation Notes / What Was Done

Implemented scoped MCP evidence retrieval and bounded correction, artifact-review, and source-stance mutations through `EvidenceReviewService`; added assistant-token audit links and an MCP schema contract. MCP can only mutate artifacts present in its operator's stored recommendation context; `original_value` is platform-captured and rejected from MCP input.

## Open Follow-Ups

- `docker compose run --rm backend ruff check mcp ai` still reports pre-existing lint failures outside task 06; focused MCP tests pass.
