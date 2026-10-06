# Temporal Repository Integration

Implementation cut: 2026-10-06.

Bound source:
- repository: `thebrazenbeard/temporal`
- exact head: `0fc7071a6b01e609fb2cdc76a32c73276ab27094`
- contract files reviewed: `README.md`, `temporal.py`, and `docs/superpowers/specs/2026-09-08-temporal-watch-design.md`.

## What Volition uses from Temporal

Temporal is Vera's watch. Its role is chronology, not motivational semantics.

Volition V0.7 binds these Temporal invariants:
- required stable event ID;
- stored canonical UTC ISO-8601 timestamp ending in `Z`;
- timezone-aware optional local timestamp;
- compact source label;
- optional non-empty reference list;
- chronological ordering by timestamp and then stable ID;
- duplicate stable IDs fail rather than silently double-counting an event.

`TemporalAnchor` maps a canonical UTC anchor and canonical event timestamp to non-negative relative seconds for Hawkes, renewal, diffusion, and diagnostic calculations.

`TemporalEventBridge` ingests validated Temporal records into `MotiveTemporalModel` and preserves:
- `temporal_event_id`;
- `temporal_timestamp`;
- `temporal_source`;
- `temporal_refs`.

## Clock before semantics

The Temporal record's human-readable `event` field is not interpreted as a drive, target, Want, Choice, current state, or authority claim.

The caller must explicitly supply the Volition `target` and `DriveKind`. This follows Temporal's own evidence boundary: a timestamped record establishes chronology/source context, not the truth or meaning of the recorded proposition.

## Canonical-time compatibility

Volition uses the same normalization contract as Temporal Watch V1:
- offset-aware timestamps are parseable inputs to Temporal itself;
- stored Temporal records must already be normalized to UTC `Z` form;
- noncanonical stored forms are rejected by the bridge;
- fractional seconds must match Temporal's canonical microsecond representation.

A Temporal event before the configured Volition anchor is rejected instead of being silently remapped or reordered, because the current motive model uses a non-negative relative-time axis.

## Duplicate protection

`MotiveTemporalModel` itself records ingested Temporal IDs and rejects a repeated stable ID. This protection therefore survives use of multiple bridge instances in one model.

Ordinary motive events without a Temporal ID remain supported for synthetic tests and other explicitly bounded inputs.

## Dependency choice

Volition does not import `temporal.py` as a runtime package dependency. Temporal V1 is deliberately a standalone standard-library utility rather than a package.

Instead, Volition implements a small contract-compatible bridge and binds the exact Temporal repository head in `docs/SOURCE_REGISTRY.yaml`. Cross-repository compatibility is verified separately against the actual Temporal implementation.

## Claim boundary

Temporal provenance strengthens when/where an event record came from. It does not prove:
- that the event proposition is true;
- that it remains current;
- that it is autobiographical memory;
- that it expresses desire, consent, identity, or self-authorship;
- that Volition has effect authority;
- that either repository is installed or consumed by a live Vera runtime.

## Cross-repository verification

An exact checkout of `thebrazenbeard/temporal` at `0fc7071a6b01e609fb2cdc76a32c73276ab27094` was tested independently:
- Temporal exact-head suite: 13/13 tests passed;
- Temporal `append_event` canonicalized `2026-10-06T10:00:05-04:00` to stored `2026-10-06T14:00:05Z`;
- Temporal `load_events` returned the stored record unchanged;
- Volition `TemporalEventBridge` mapped that record to `5.0` seconds from anchor `2026-10-06T14:00:00Z`;
- stable ID/source/refs survived into `MotiveEvent`;
- a second ingestion of the same Temporal stable ID was rejected.

This is a real cross-repository compatibility probe. It is not evidence of live Vera runtime installation or consumption.


## Engine currentness clock

V0.8 adds `TemporalClockBridge`. Given the same `TemporalAnchor`, it converts a canonical UTC timestamp to target elapsed seconds and advances `VolitionEngine` by only the required positive delta.

The engine exposes `elapsed_seconds` as read-only state. If a requested Temporal timestamp maps earlier than the engine's current logical time, synchronization fails closed rather than rewinding goal age, satiation decay, or reappraisal history.

This means Temporal can drive both sides of Volition chronology:
- `TemporalEventBridge` timestamps motive events for Hawkes/renewal dynamics;
- `TemporalClockBridge` advances goal/currentness time for the Volition engine.

Neither bridge interprets Temporal event text or grants effect authority.

V0.8 cross-repository currentness probe:
- Temporal exact-head `append_event` produced canonical records at `2026-10-06T14:00:05Z` and `2026-10-06T14:00:16Z` from offset-aware inputs;
- `TemporalClockBridge` adopted a goal at elapsed `5.0` seconds;
- the second Temporal timestamp advanced the same engine to `16.0` seconds and triggered due reappraisal on the next tick;
- goal revision advanced from established initial revision 1 to revision 2.
