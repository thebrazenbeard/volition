# Historical Motive Evidence Integration

Implementation cut: 2026-10-06.

Bound source: `thebrazenbeard/conations` at `51948aac796936f0e7c437722e6f52c883e544e9`.

Reviewed exact-head contracts: `README.md`, `CONATION_WORKSPACE.md`, and `EVENT_INDEX.md`.

## Contract

The source repository is append-only lifecycle evidence. Stored status labels describe their original evidence cut and are not automatically current later.

`ConationRecord` is a normalized record containing a stable ID, explicit Volition target, explicit drive family, bounded magnitude/confidence, lifecycle status, and source locator. The bridge does not infer target or drive family from free-form source text.

`ConationBridge.historical_signal(...)` always emits `HISTORICAL_EVIDENCE` with `current_reappraisal=False`. Volition therefore assigns it zero motive value until fresh current evidence exists.

## Fresh reappraisal

`ConationBridge.reappraise(record, current_signal)` requires a separate `CURRENT_STATEMENT` or `CURRENT_OBSERVATION` signal with the same target and drive family and an explicit source.

The historical contribution remains labeled historical and is capped by the fresh evidence:
- old magnitude cannot exceed current magnitude;
- old confidence cannot exceed current confidence.

Per-drive-family max arbitration prevents the archived record from amplifying a weaker present signal.

## Lifecycle boundaries

Records marked `COMPLETED`, `REVOKED`, `CONTRADICTED`, or `REVISED` cannot be directly reactivated through this bridge. A later state is new evidence.

`HISTORICAL / UNRESOLVED` and `CONSTRAINT-AFFECTED / UNEXPRESSED-UNCERTAIN` remain historical without being rewritten to zero. They still contribute zero current motive value until separately corroborated.

## Output boundary

The bridge supplies evidence to normal Volition evaluation. It does not create a Choice or Goal and does not change effect authority.

This implements the source repository's central currentness rule: stored history is evidence for reappraisal, not a standing current state.
