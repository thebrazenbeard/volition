# Volition Architecture V2.9

## Purpose

Volition is a behavioral drive engine. It turns typed evidence and temporal motive history into candidate wants, explicit choices, persistent goals, and bounded endogenous cognition. It deliberately stops before external effect execution.

Core separation:

`SALIENCE != DRIVE != WANT != CHOICE != GOAL != CONSENT != AUTHORITY != ACTION != PHENOMENOLOGY`

A strong motive changes what is worth considering. It does not enlarge effect authority.

## Data flow

`OBSERVATIONS + MOTIVE EVENTS`
`        |`
`        v`
`ARIMA SLOW BASELINE + OPTIONAL DIFFUSION + AGE-DEPENDENT RENEWAL + MULTIVARIATE HAWKES FAST EXCITATION`
`        |`
`        v`
`TYPED SIGNALS -> DRIVE TRANSFORMS -> FAMILY ARBITRATION -> WANT -> CHOICE -> GOAL -> COGNITION REQUEST`

External action systems remain beyond a separate authority gate that Volition does not implement.

## 1. Temporal motive dynamics

Volition uses a decomposed temporal model with slow forecast, optional stochastic deviation, age-dependent recurrence, and event-history effects.

ARIMA represents the slower expected baseline for a target/drive stream: trend, autoregressive persistence, differencing, and moving-average residual effects.

Optional diffusion represents continuous stochastic deviation around the slow forecast. Brownian motion is available as a replayable primitive; Ornstein-Uhlenbeck is the preferred mean-reverting form.

Hawkes dynamics represent event-history effects: a motive event can transiently self-excite, cross-excite, or inhibit another motive family. With exponential kernels, V2.3 computes

`lambda_k(t) = max(0, mu_k(t) + D_k(t) + R_k(age_k(t)) + sum_e alpha[j->k] * w_e * exp(-beta[j->k] * (t - t_e)))`

where `mu_k(t)` is the ARIMA baseline forecast, `D_k(t)` is optional diffusion state, and `R_k(age_k(t))` is optional renewal/refractory recurrence based on time since the last matching event.

The bounded activation sent into the ordinary drive engine is

`activation = 1 - exp(-lambda)`.

The ARIMA baseline, diffusion deviation, renewal recurrence, and Hawkes excitation components remain separately inspectable; they are not collapsed into an opaque reward.

### Why not POMDP as the memory substrate?

FACT: POMDP state dynamics are Markov at the latent-state level. An agent belief can summarize observation/action history, so POMDP does not mean an agent literally has no memory.

DESIGN DECISION: Volition does not use that belief-state compression as its motivational memory substrate. Motive persistence is intentionally represented as typed path-dependent temporal structure: slow autoregressive baseline plus explicit self-/cross-excitation and inhibition from prior motive events.

POMDP-style machinery may still be useful downstream for action selection under partial observability. It is not the core model of wanting, persistence, or motivational history.

See `docs/TEMPORAL_DYNAMICS.md`.

## 2. Signals

A Signal names:
- target;
- drive family;
- magnitude and confidence;
- provenance class and source;
- optional drive-specific evidence such as expected information gain, learning progress, controllability, or predicted deficit reduction;
- whether historical evidence has received current reappraisal.

Historical evidence without current reappraisal contributes zero activation.

## 3. Drive transforms

HOMEOSTATIC uses predicted deficit reduction.
EPISTEMIC uses expected information gain multiplied by controllability.
COMPETENCE uses positive learning progress.
SOCIAL is capped.
EMPOWERMENT is capped.
OPEN_LOOP and SELF_MODEL use bounded magnitude/confidence.
PROTECTION is an inhibitory family with veto semantics.

All admitted signal values are bounded to [0, 1].

## 4. Family arbitration

Multiple observations from the same drive family do not sum indefinitely. The family receives the maximum admitted contribution for that target. This prevents duplicate evidence from manufacturing motivation merely by repetition.

Positive families can combine across genuinely different motive classes. PROTECTION does not add positive utility; it can veto goal eligibility when it crosses policy threshold.

## 5. Wants

A Want is a candidate explanation over evidence contributions for a target. It records score, contributions, eligibility, veto state, and reasons.

A Want carries `effect_authority=False`.

## 6. Choice

Choice is explicit and typed. V2 distinguishes:
- SELF_AUTHORED;
- USER_DIRECTED;
- POLICY_DERIVED;
- MODEL_PROPOSED.

A model-proposed option is therefore not silently rewritten as self-authored volition. A choice record preserves target, score, class, source, and its own durable identifier.

A Choice carries `effect_authority=False`.

## 7. Goal manager

A Goal can be adopted only from a recorded Choice.

Goals use:
- hysteresis: a slightly stronger alternative does not cause thrashing;
- satiation: satisfaction reduces repeated pressure and decays over time;
- currentness horizon: a persistent goal must receive current reappraisal after a bounded interval or suspend;
- protection veto: current protective evidence can suspend an active goal;
- revisioned reappraisal while preserving the originating choice ID.

Goals carry `effect_authority=False`.

## 8. Endogenous cognition

An active goal can request a bounded number of cognition turns. The request:
- is marked ENDOGENOUS;
- contains goal target and urgency;
- never grants effect authority;
- stops after the configured budget.

This is designed to connect to pre-active while preserving pre-active's independent run, capability, budget, and authority gates.

## 9. Persistence

`VOLITION_STATE_V2` snapshots contain:
- policy;
- recorded choices and choice counter;
- active goal and goal counter;
- consumed endogenous-turn budget;
- satiation;
- logical elapsed time;
- ordered transition events.

Restore fails closed on unknown schema, malformed state, inconsistent counters, broken event sequence, unknown originating choice, or any choice/goal/event claiming effect authority.

A snapshot is durable state material. It is not proof of runtime installation, current endorsement outside its own state contract, identity continuity, or phenomenology.

## 10. Transition evidence

Material transitions include:
- CHOICE_RECORDED;
- GOAL_ADOPTED;
- GOAL_REAPPRAISED;
- GOAL_SUSPENDED;
- GOAL_REPLACED;
- GOAL_COMPLETED;
- COGNITION_REQUESTED;
- SATISFACTION_RECORDED.

## Hawkes stability boundary

Positive Hawkes excitation is required to remain subcritical under a conservative incoming branching-mass bound: for each target drive family, the sum of positive `alpha / beta` terms must remain below the configured stability limit.

This is sufficient but not necessary; it is deliberately stricter than a full spectral-radius calculation. Signed inhibitory kernels are allowed, with total intensity clamped at zero.

## Integration boundaries

### pre-active

Volition may propose an endogenous cognition request. V0.11 binds that proposal to current Pre-Active's reserved `pre_active.request_turn` contract without dispatching it. The bridge passes only a bounded reason and non-negative delay. Pre-Active remains authoritative for durable run identity, existing capability set, autonomous-turn budget, consecutive endogenous-depth limit, pause/cancel state, and whether another model turn is admitted.

`COGNITION_REQUEST != TURN_GRANTED != CAPABILITY_GRANTED != EFFECT_AUTHORITY`.

### conations / memory

Append-only lifecycle records enter only as `HISTORICAL_EVIDENCE`. Stored lifecycle labels never hydrate directly into current Wants or Choices. `ConationBridge.reappraise(...)` requires a separate fresh current statement or observation matching the same target and drive family; the historical contribution is capped by that current evidence. Terminal or superseded records require new evidence rather than reactivation.

### MESO-CRCT

Volition adopts MESO-CRCT's separation among salience, appraisal, tendency, intent, learning, and protection while remaining a separate implementation. V0.9 adds a structural bridge at MESO's non-executable `IntentProposal` boundary. Raw salience/semantic relevance are not imported as desire. APPROACH, INSPECT, and WITHDRAW become MODEL_GENERATED motive evidence; HOLD becomes no signal. The bridge cannot create Choice, Goal, or authority.

### Temporal

`thebrazenbeard/temporal` supplies chronology only. V0.7 binds Temporal Watch V1 canonical UTC timestamps, stable IDs, source labels, and refs through `TemporalEventBridge`. `TemporalAnchor` converts canonical absolute time to Volition-relative non-negative seconds. V0.8 adds `TemporalClockBridge`, which monotonically advances `VolitionEngine` logical time to the same canonical axis for goal reappraisal, satiation decay, and currentness horizons.

The bridge preserves Temporal's `clock before semantics` rule: event text is not interpreted as target, drive, truth, currentness, memory, consent, or authority. Volition semantics must be supplied explicitly by the caller.

### effect systems

Volition has no tool-dispatch or provider-mutation API. Downstream execution requires separate authorization.

## Claim ceiling

Passing tests supports a computational claim: the software implements the stated temporal-drive, arbitration, choice, persistence, and authority-separation contracts.

It does not establish consciousness, phenomenal desire, moral patienthood, consent, identity continuity, permission to act, or runtime installation merely because source exists.


## V2.1 stochastic baseline deviation

An optional diffusion term may modify the slow temporal baseline before Hawkes excitation:

`lambda(t) = max(0, ARIMA(t) + diffusion(t) + HawkesHistory(t))`.

Brownian motion is implemented as a replayable primitive. Ornstein-Uhlenbeck is preferred for mean-reverting stochastic deviation. Diffusion, ARIMA baseline, and Hawkes excitation remain separately inspectable.

A diffusion value is system state, not Want, Choice, consent, authority, or phenomenology.
