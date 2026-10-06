# Pre-Active Re-entry Integration

Implementation cut: 2026-10-06.

Bound source:
- repository: `thebrazenbeard/pre-active`
- exact current head: `a6900dc2d2fb65f4ea66db95fca1b9c5b022450b`
- currentness correction: the prior Volition registry pin `94cb3b8044d7a4263c50a96bfecfcfebc5533716` was superseded before this bridge was implemented.

Reviewed current-head contracts include:
- `README.md`;
- `docs/AUTONOMOUS_RUNTIME.md`;
- `src/pre_active/engine.py` reserved `pre_active.request_turn` contract;
- `src/pre_active/store.py` autonomous-turn and same-run deferral paths;
- `src/pre_active/initiative.py` bounded initiative-policy layer.

## Boundary

Volition decides whether an active Goal warrants another bounded cognition turn. Pre-Active decides whether and how that turn is admitted into its durable runtime.

`VolitionEngine.request_cognition()` returns a `CognitionRequest`. `PreActiveCognitionBridge.from_request(...)` converts only an `ENDOGENOUS`, non-authoritative request into a `PreActiveReentryProposal` targeting the reserved `pre_active.request_turn` primitive.

The bridge is deliberately non-dispatching. It does not:
- enqueue an event;
- create or select a Pre-Active run;
- add capabilities;
- produce a request/event/run identifier;
- bypass Pre-Active autonomous-turn budgets or endogenous-depth limits;
- mutate provider, filesystem, network, credential, or effect state.

## Reserved tool contract

The proposal contains only the fields accepted by current Pre-Active:
- `reason`: bounded non-empty text;
- `delay_seconds`: finite non-negative delay.

The target tool is exactly `pre_active.request_turn`. At the bound Pre-Active head that tool is classified:
- capability: `pre_active.internal.autonomy`;
- mutation: `False`.

Pre-Active's runtime, not Volition, owns the reserved capability and decides whether the tool remains advertised for the current run. When the consecutive endogenous-depth or autonomous-turn budget is exhausted, Volition's desire for another cognition turn does not override the runtime fence.

## Same-run semantics

Current Pre-Active preserves endogenous re-entry on the same durable run. A valid deferral changes a run from `RUNNING` to `WAITING`, increments the run step and autonomous-turn count, and creates a successor `run.step` event with source `ENDOGENOUS`.

The existing run capability set is preserved exactly. Re-entry therefore means:

`COGNITION_REQUEST != NEW_RUN != NEW_CAPABILITY != EFFECT_AUTHORITY`

## Currentness

Pre-Active advanced materially on 2026-10-06 before this integration. The new current head includes durable observers and temporal initiative models, including a subcritical exponential Hawkes threshold policy. Volition does not import or duplicate that policy as another motive generator.

The two Hawkes uses remain separate:
- Volition Hawkes: motive-event history contributing to typed motive intensity;
- Pre-Active Hawkes threshold: host initiative policy deciding whether an observed change warrants a model turn.

A Pre-Active initiative decision is therefore not silently converted into a Volition Want, and a Volition Want is not sufficient to force Pre-Active to wake.

## Cross-repository verification

Against exact Pre-Active head `a6900dc2d2fb65f4ea66db95fca1b9c5b022450b`:
- the exact-head test suite completed without failure;
- the Volition proposal matched `AUTONOMOUS_TURN_TOOL_NAME`;
- Pre-Active's own reserved-tool parser accepted the proposal arguments;
- a durable run created with capabilities `files.read` and `github.read` entered `WAITING` through Pre-Active's own `defer_run_for_autonomous_turn(...)` path;
- those capabilities remained unchanged;
- `autonomous_turn_count` increased by one;
- the successor `run.step` retained the same run ID and source `ENDOGENOUS`.

## Claim ceiling

This demonstrates source-level and packaged-contract compatibility. It does not establish that a Pre-Active daemon is installed, running, connected to Volition, or granting live autonomous turns in Vera.
