# Volition

Volition is a governed behavioral drive engine for AI agents: internally generated wants, typed choices, persistent goals, temporal motive dynamics, and bounded self-initiated cognition.

It is built to make reactive models more proactive without collapsing motivation into permission.

`SALIENCE != DRIVE != WANT != CHOICE != GOAL != CONSENT != AUTHORITY != ACTION != PHENOMENOLOGY`

## Foundation V2.1

The current work branch implements:
- eight typed motive families: homeostatic, epistemic, competence, empowerment, open-loop, social, self-model, and protection;
- provenance/currentness gating for historical evidence;
- bounded family arbitration so repeated evidence cannot self-amplify;
- protection vetoes;
- explicit Choice records distinguishing SELF_AUTHORED, USER_DIRECTED, POLICY_DERIVED, and MODEL_PROPOSED;
- goal hysteresis, satiation/recovery, and periodic current reappraisal;
- bounded ENDOGENOUS cognition requests;
- `VOLITION_STATE_V2` snapshot/restore with choice provenance;
- ordered transition receipts;
- ARIMA slow-baseline motive forecasts;
- multivariate Hawkes self-/cross-excitation and inhibition;
- optional replayable Brownian diffusion and mean-reverting Ornstein-Uhlenbeck diffusion;
- conservative subcriticality checks against runaway excitation;
- hard `effect_authority=False` boundaries throughout.

## Temporal model

Volition does not use POMDP belief state as its motivational memory substrate.

POMDP latent dynamics are Markov, although a belief state can summarize history. Volition instead keeps motivational dynamics explicit:

`ARIMA slow baseline + optional diffusion + Hawkes event-history excitation/inhibition -> typed Signal -> Want -> Choice -> Goal`

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

## Research basis

Internal sources include pre-active, conations, MESO-CRCT, Vera, the control plane, empathy, Semantic Atlas, DeepMemory, Selfimage, Temporal, and Project Runner. Sexuality/Orgasm contribute only abstract public-safe mechanisms; intimate material is not copied into Volition.

External research includes autotelic goal generation, homeostatic RL, epistemic value, curiosity/learning progress, BDI separation, Hawkes processes, ARMA/CARMA-Hawkes work, Brownian/SDE-driven Hawkes variants, self-limiting Hawkes models, and ARIMA reference implementations.

See:
- `docs/INTERNAL_SYNTHESIS.md`
- `docs/EXTERNAL_RESEARCH.md`
- `docs/EXTERNAL_PRIOR_ART.md`
- `docs/TEMPORAL_DYNAMICS.md`
- `docs/MODEL_SELECTION.md`
- `docs/SOURCE_REGISTRY.yaml`
- `docs/ARCHITECTURE.md`
- `docs/HOSTILE_REVIEW.md`

## Status

FOUNDATION_V2_1_DIFFUSION_IMPLEMENTED_AND_TESTED_ON_WORK_BRANCH

This does not mean merged to `main`, installed into a runtime, behaviorally qualified in a live agent, or independently reviewed.


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
