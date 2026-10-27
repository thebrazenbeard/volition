# Volition

Volition is a governed behavioral drive engine for AI agents: internally generated wants, typed choices, persistent goals, temporal motive dynamics, and bounded self-initiated cognition.

It is built to make reactive models more proactive without collapsing motivation into permission.

`SALIENCE != DRIVE != WANT != CHOICE != GOAL != CONSENT != AUTHORITY != ACTION != PHENOMENOLOGY`

## Foundation V2.8

The current work branch implements:
- eight typed motive families: homeostatic, epistemic, competence, empowerment, open-loop, social, self-model, and protection;
- provenance/currentness gating for historical evidence;
- bounded family arbitration so repeated evidence cannot self-amplify;
- protection vetoes;
- explicit Choice records distinguishing SELF_AUTHORED, USER_DIRECTED, POLICY_DERIVED, and MODEL_PROPOSED;
- goal hysteresis, satiation/recovery, and periodic current reappraisal;
- bounded ENDOGENOUS cognition requests;
- `VOLITION_STATE_V3` snapshot/restore with choice provenance and scored reappraisal receipts;
- ordered transition receipts;
- Temporal Watch V1 bridge for canonical UTC chronology, stable event IDs, and event provenance;
- Temporal-driven engine clock for goal reappraisal and satiation/currentness timing;
- MESO-CRCT non-executable intent bridge with salience and authority firewalls;
- append-only lifecycle-history bridge with mandatory fresh-current reappraisal;
- ARIMA slow-baseline motive forecasts;
- multivariate Hawkes self-/cross-excitation and inhibition;
- optional replayable Brownian diffusion and mean-reverting Ornstein-Uhlenbeck diffusion;
- age-dependent renewal/refractory recurrence hazard;
- homogeneous Poisson null-model calibration;
- martingale residual and time-rescaling point-process diagnostics;
- distributional screening of time-rescaled intervals via Uniform-transform KS distance and lag-1 correlation;
- conservative subcriticality checks against runaway excitation;
- hard `effect_authority=False` boundaries throughout.

## Temporal model

Volition does not use POMDP belief state as its motivational memory substrate.

POMDP latent dynamics are Markov, although a belief state can summarize history. Volition instead keeps motivational dynamics explicit:

`ARIMA slow baseline + optional diffusion + renewal/refractory age hazard + Hawkes event-history excitation/inhibition -> typed Signal -> Want -> Choice -> Goal`

That makes recurrence, cross-excitation, decay, and slow drift first-class rather than burying them inside a generic state belief.

See `docs/TEMPORAL_DYNAMICS.md`.

## Minimal example

```python
from volition import (
    ARIMABaseline,
    DriveKind,
    HawkesKernel,
    MotiveTemporalModel,
    VolitionEngine,
)

temporal = MotiveTemporalModel(
    kernels=[
        HawkesKernel(
            source_kind=DriveKind.OPEN_LOOP,
            target_kind=DriveKind.OPEN_LOOP,
            alpha=0.2,
            beta=0.5,
        )
    ]
)
temporal.set_baseline(
    "investigate-unresolved-question",
    DriveKind.OPEN_LOOP,
    ARIMABaseline(intercept=0.25, ar=(0.5,), difference_order=0),
)
temporal.observe_event(
    "investigate-unresolved-question",
    DriveKind.OPEN_LOOP,
    at_seconds=0.0,
)

signal = temporal.signal(
    "investigate-unresolved-question",
    DriveKind.OPEN_LOOP,
    at_seconds=1.0,
)

engine = VolitionEngine()
want = engine.evaluate([signal])[0]
choice = engine.choose(
    want,
    choice_class="MODEL_PROPOSED",
    source="model:deliberation",
)
goal = engine.adopt_choice(choice.choice_id)
request = engine.request_cognition()
```

The cognition request is a reason to think again. It is not authorization to perform an external effect.

## Opt-in persistent operational motivation

`OperationalMotivation` adds a replay-safe, serialized operational-want register
without changing existing `VolitionEngine.tick()` callers. A model proposes a
target and a drive family; an *external integration caller* supplies and
allowlists a matching current observation. The observation, **not** model prose,
determines urgency. The new goal's Choice is explicitly `MODEL_PROPOSED`, never
`SELF_AUTHORED`. `effect_authority` remains false.

```python
from hashlib import sha256
from volition import (
    DriveKind, ModelWantProposal, ObservationClaim,
    ObservationVerifier, OperationalMotivation,
)

evidence = b"observer-measured:unanswered-work-item:73"
claim = ObservationClaim(
    evidence_id="observer-event-73",
    content_digest="sha256:" + sha256(evidence).hexdigest(),
    target="resolve-work-item-73", kind=DriveKind.OPEN_LOOP,
    magnitude=0.8, confidence=0.9, source_ref="trusted-observer:item-73",
)
# The host MUST independently verify the observation before creating this allowlist.
admitted = ObservationVerifier([claim], verifier_id="operator:monitor").admit(claim)
motivation = OperationalMotivation()
goal = motivation.propose(ModelWantProposal(
    proposal_id="model-proposal-73", target=claim.target,
    kind=claim.kind, evidence_id=claim.evidence_id,
    reason="bounded examination of the unresolved discrepancy",
), admitted)
request = motivation.request_cognition() if goal is not None else None
state = motivation.snapshot()  # Persist atomically via the integrating host.
restored = OperationalMotivation.from_snapshot(state)
```

Distinct evidence IDs **and** canonical content SHA-256 digests prevent
replaying one observation as another drive family or newly numbered event.
Repeated proposals yield no new goal/cognition trigger, including after a
reappraisal horizon and snapshot restore. New observations lower or suspend
stale goal urgency; a protection veto latches across restart until an
independently caller-admitted *new* zero-protection observation clears it.
Completion requires the existing exact `AdmittedGoalCompletion` contract via
`motivation.complete(receipt)` and cannot resurrect the prior evidence.

**Scope:** This is a local, host-opt-in decision and motivation primitive.
It does not schedule itself, poll sensors, verify remote attestations, acquire
authority, dispatch actions, or provide evidence of subjective desire. The
caller allowlist provides chain-of-custody only at that caller's trust level;
neither SHA-256 nor the presence of a verifier ID authenticates observations.
The persistent replay ledger has a finite capacity and fails closed when full.

## Versioned goal-completion boundary

As of package `0.11.0`, `record_satisfaction(target, amount)` changes only
bounded, decaying target satiation. It **never** completes a goal from a
target-only scalar. `complete_goal(...)` instead requires an exact
`AdmittedGoalCompletion` with current goal ID, choice ID, goal revision, target,
unique outcome event ID, result receipt, evidence reference, and caller-admitted
current-source provenance. Replays are checked against persisted transition
events; completed goals cannot be restored as active. This contract grants no
tool authority and provides **caller-selected admission, not independent
source authentication**. Raw Pre-Active outcome candidates are not admitted.

See `docs/GOAL_COMPLETION_ADMISSION_V1.md` for the acceptance criteria and
remaining evidence-custody limitations.

## Typed and numeric input boundary

`VolitionEngine.evaluate()` accepts `Signal` instances whose `kind` and
`provenance` are actual `DriveKind` and `ProvenanceClass` members. Raw strings
that merely equal enum values are rejected: otherwise identity-based historical
currentness and drive-family calculations could be bypassed. All signal numeric
fields must be actual numeric types and finite; ordinary finite magnitudes retain
their existing bounded clamping behavior. The five normalized policy thresholds
and caps require values in `[0, 1]`; the time parameters and restored
snapshot numeric state reject non-finite input and coerced Boolean/string
numbers. Snapshot choice/goal scores and satiation must lie in `[0, 1]`.
Signal target and source must be nonblank strings. `choose()` and `adopt()`
accept only an unchanged `Want` object produced by the engine's latest
`evaluate()` call, consumed at most once. Time, satiation, goal adoption, and
cognition-budget changes invalidate outstanding evaluated wants. This is
process-local evidence of arbitration, **not** a
cryptographic proof of upstream signal custody or external action permission.
`adopt_choice()` additionally requires a recorded Choice that is still pending
from the current evaluation and has not been adopted before. A new evaluation,
state advancement, or goal adoption invalidates pending choices; restored
snapshots retain Choice history but require fresh arbitration before adoption.
Clock advances check the accumulated time for overflow before modifying state.
The endogenous
cognition budget must be a nonnegative integer.
Restore additionally checks strictly typed nonnegative integer counters and
event sequences; engine-generated choice/goal IDs must not exceed their
counter. An active goal must preserve its originating Choice's target; its
adoption score must match the Choice on revision 1. Later revisions require
matching ordered `GOAL_REAPPRAISED` events **with scores** matching the restored
goal, since genuine reappraisal can change its score. Legacy V2 snapshots with
an active goal past revision 1 now fail closed: their events did not record
scores, so the revised score cannot be verified. Legacy V2 unrevised or
inactive snapshots remain readable and re-export under V3. See
`docs/REAPPRAISAL_SCORE_V3.md`. Goal/transition timestamps cannot exceed the
restored logical clock or run backward.

This validation protects the deterministic arbitration and persistence
contracts. It does **not** authenticate a caller's claim that a current
observation occurred, independently verify historical reappraisal, or grant
permission to perform an external effect.

`Volition Python CI` checks the full `pytest` suite on Python 3.11–3.13;
this is source/build evidence, not a host runtime attestation.

## Research basis

Internal sources include pre-active, conations, MESO-CRCT, Vera, the control plane, empathy, Semantic Atlas, DeepMemory, Selfimage, Temporal, and Project Runner. Sexuality/Orgasm contribute only abstract public-safe mechanisms; intimate material is not copied into Volition.

External research includes autotelic goal generation, homeostatic RL, epistemic value, curiosity/learning progress, BDI separation, Hawkes processes, ARMA/CARMA-Hawkes work, Brownian/SDE-driven Hawkes variants, age-dependent and renewal-Hawkes models, self-limiting Hawkes models, and ARIMA reference implementations.

See:
- `docs/INTERNAL_SYNTHESIS.md`
- `docs/MESO_INTEGRATION.md`
- `docs/CONATION_INTEGRATION.md`
- `docs/EXTERNAL_RESEARCH.md`
- `docs/EXTERNAL_PRIOR_ART.md`
- `docs/TEMPORAL_DYNAMICS.md`
- `docs/TEMPORAL_INTEGRATION.md`
- `docs/RENEWAL_DYNAMICS.md`
- `docs/MODEL_SELECTION.md`
- `docs/SOURCE_REGISTRY.yaml`
- `docs/ARCHITECTURE.md`
- `docs/HOSTILE_REVIEW.md`

## Status

FOUNDATION_V2_8_HISTORY_CURRENTNESS_BRIDGE_CANONICAL_ON_MAIN

Canonical source is now on `main`. Source presence still does not by itself prove runtime installation, live behavioral qualification, or independent review.


## V2.1 diffusion extension

The temporal stack now optionally includes a replayable diffusion term:

`ARIMA baseline + Brownian/OU diffusion + Hawkes history -> typed Signal`

Raw Brownian motion is available as a stochastic innovation primitive. Ornstein-Uhlenbeck is the preferred optional diffusion when the deviation should mean-revert instead of wandering without bound.

The caller supplies each realized innovation explicitly; Volition does not hide random sampling inside the engine. See `docs/TEMPORAL_DYNAMICS.md` and `docs/MODEL_SELECTION.md`.

Current full regression after this extension: 33 tests passing before exact-head closeout.


## V0.4 calibration diagnostics

The package now includes a homogeneous Poisson null model, numerical compensator, and martingale residual diagnostics for event-arrival calibration.

These are evaluation tools only. They cannot directly alter drive scores, Choice classes, Goals, or authority.

See `docs/DIAGNOSTICS.md`.


V0.4 also exposes `time_rescaled_intervals(...)`, which maps observed event gaps through integrated model intensity. This is the transformation primitive; distributional goodness-of-fit testing remains separate.


## V0.5 renewal/refractory dynamics

The temporal stack now optionally models age since the last matching motive event. `RefractoryRenewalHazard` can impose an absolute refractory window and then recover recurrence hazard toward an asymptotic rate.

This recurrence term is separate from Hawkes excitation and from engine-level satiation. See `docs/RENEWAL_DYNAMICS.md`.


## V0.6 rescaling distribution diagnostics

Volition now evaluates time-rescaled intervals without issuing a binary model-validity verdict. `evaluate_time_rescaled_intervals(...)` reports interval mean/variance, the Uniform-transform Kolmogorov-Smirnov distance, lag-1 correlation when defined, and transformed Uniform values.

No p-value is manufactured. These are screening statistics and remain diagnostic-only.


## V0.7 Temporal Watch integration

Volition now consumes Temporal Watch V1 records through `TemporalEventBridge`. Canonical UTC timestamps are converted to the model's non-negative relative-time axis, while stable Temporal IDs/source/refs remain attached to each `MotiveEvent`.

The Temporal record's human-readable event text is never used to infer a motive target or drive. See `docs/TEMPORAL_INTEGRATION.md`.


## V0.8 Temporal currentness clock

`TemporalClockBridge` advances `VolitionEngine` logical time to a canonical Temporal UTC timestamp without maintaining a second hidden clock. The engine exposes read-only `elapsed_seconds`; clock rewinds fail closed. Goal reappraisal horizons and satiation decay can therefore use the same canonical chronology as Temporal motive events.


## V0.9 MESO-CRCT intent bridge

`MesoIntentBridge` accepts MESO-CRCT's non-executable `IntentProposal` contract only. APPROACH maps to open-loop evidence, INSPECT to epistemic evidence, WITHDRAW to protection, and HOLD to no signal. Raw salience is not admitted and bridge output remains `MODEL_GENERATED` evidence rather than Choice or authority. See `docs/MESO_INTEGRATION.md`.


## V0.10 Historical currentness bridge

`ConationBridge` admits append-only lifecycle records as historical evidence only. Stored PRESENT labels remain non-current until separately corroborated by a fresh current statement or observation. Reappraised historical strength is capped by the fresh evidence, and terminal or superseded records cannot be silently reactivated. See `docs/CONATION_INTEGRATION.md`.
