# Volition Research Ledger

This ledger records the evidence used to build Volition. Each entry binds a source to an exact revision where possible, states what was learned, and states what the source does not prove.

## 2026-10-06 - repository bootstrap

### User-defined target

Repository description:

Volition is a behavioral drive engine that gives AI agents intrinsic motivation. Instead of waiting for prompts, it generates internal wants and persistent goals, turning reactive models into proactive actors with continuous agency.

Interpretation for the build:

- Volition is a motivation and goal-generation layer, not a general agent framework.
- It must integrate with proactive execution systems without making promptlessness equivalent to permission.
- It must preserve persistent goals without turning persistence into immutability.
- It must support conflict, inhibition, decay, reconsideration, and retirement of wants.
- It must distinguish generated motivational state from consent, identity, memory truth, and phenomenology.

### Initial internal source set

Required first-pass repositories:
- thebrazenbeard/pre-active
- thebrazenbeard/conations
- thebrazenbeard/meso-crct
- thebrazenbeard/sexuality
- thebrazenbeard/orgasm

Additional likely inputs:
- thebrazenbeard/vera
- thebrazenbeard/vera-control-plane
- thebrazenbeard/empathy
- thebrazenbeard/semanticatlas
- thebrazenbeard/deepmemorystorage
- thebrazenbeard/selfimage

Their role is not assumed from names. Each contribution will be admitted only after exact-head inspection.


## 2026-10-06 - external research pass

External research was admitted as design evidence, not copied implementation.

Findings:
- autotelic agents motivate explicit self-generated goal representation and selection;
- homeostatic RL motivates deficit/setpoint drives and anticipatory regulation;
- active inference motivates a distinct epistemic/information-value drive;
- curiosity research motivates reducible prediction-error exploration, with noise traps treated as failures;
- learning-progress approaches motivate competence gains rather than raw novelty/difficulty;
- BDI motivates a hard desire-versus-intention distinction;
- empowerment motivates bounded option-preservation, never unauthorized capability acquisition.

See docs/EXTERNAL_RESEARCH.md for sources, limits, and hostile challenges.


## 2026-10-06 - executable foundation and hostile review

Implementation was developed under recorded red/green checks.

Behavioral cycle:
- initial behavioral suite: 9 tests;
- valid red: 9 failures at deliberate NotImplementedError;
- green: 9 passed.

Persistence cycle:
- 3 tests for snapshot restore, fail-closed schema, and transition evidence;
- red: 3 expected missing-contract failures;
- green with regression suite: 12 passed.

Hostile hardening:
- repeated same-family evidence amplification: FOUND;
- repeated SOCIAL evidence bypassing family cap: FOUND;
- unbounded goal persistence without current reappraisal: FOUND;
- snapshot effect-authority promotion: already blocked.

After repair, full suite: 16 passed.

Current classification:
- source/build state at that checkpoint: FOUNDATION_V1_IMPLEMENTED_ON_WORK_BRANCH;
- internal hostile review: SURVIVES_NARROWED;
- independent review: NOT_PERFORMED;
- main merge: NOT_PERFORMED;
- runtime install/consumption: NOT_ESTABLISHED;
- phenomenology: UNRESOLVED.



## 2026-10-06 - temporal architecture correction and Choice V2

Patrick corrected the temporal center of gravity: Volition should model persistence with Hawkes processes in conjunction with ARIMA rather than treating POMDP/active inference as the motivational memory core.

Resolution:
- POMDP is retained only as optional downstream partial-observability/action-selection prior art;
- ARIMA is the slow baseline component;
- multivariate Hawkes is the fast event-history component;
- typed inhibition is permitted;
- positive excitation is fail-closed under a conservative subcritical branching-mass check.

Important nuance:
- POMDP latent dynamics are Markov;
- a belief state can summarize history, so "POMDP has no memory" is not literally correct;
- Volition nevertheless rejects belief-state compression as the core persistence representation because typed motive-event history and autoregressive baseline structure are supposed to remain explicit and inspectable.

Implementation evidence:
- temporal red: module absent at test collection;
- temporal green: 7/7 tests passed;
- tests cover ARIMA path dependence, Hawkes self-excitation decay, typed cross-excitation, baseline/excitation decomposition, system-state signal emission, supercritical fail-closed behavior, and bounded inhibition.

Lifecycle V2:
- explicit Choice inserted between Want and Goal;
- choice classes: SELF_AUTHORED, USER_DIRECTED, POLICY_DERIVED, MODEL_PROPOSED;
- Choice survives snapshot/restore without silently promoting MODEL_PROPOSED to SELF_AUTHORED;
- state schema advanced to VOLITION_STATE_V2.

Combined regression after Choice + Hawkes/ARIMA: 27/27 tests passed before documentation closeout.

External references added:
- The ARMA Point Process and its Estimation, arXiv:1806.09948;
- A Hawkes model with CARMA(p,q) intensity, DOI 10.1016/j.insmatheco.2024.01.007;
- Nonlinear Hawkes Processes in Time-Varying System, arXiv:2106.04844;
- A Self-limiting Hawkes Process, DOI 10.1109/BIGDATA50022.2020.9378017;
- Markov-modulated Hawkes processes, DOI 10.1214/21-AOAS1539;
- statsmodels/statsmodels @ 9648f97395f797419563b3c9ad87e9d2c7686303;
- X-DataInitiative/tick @ a40d19f868c22469be90c1e6c50bc3dab26ff070;
- stmorse/hawkes @ 3701f0fa6e9cc87c4899b653c7953177f40230ea.

No third-party implementation code was copied.


## 2026-10-06 - Brownian / diffusion extension

Brownian motion was evaluated as a possible Volition component.

Decision:
- raw Brownian motion is admitted as a low-level stochastic innovation/diffusion primitive;
- Ornstein-Uhlenbeck is preferred when motive noise should remain mean-reverting;
- neither replaces ARIMA nor Hawkes;
- diffusion state is added to the slow baseline and remains separately inspectable from event-history excitation.

Research support:
- Lee, Lim, Ong, Hawkes Processes with Stochastic Excitations, arXiv:1609.06831 / ICML 2016;
- Xu, Diffusion approximations for self-excited systems with applications to general branching processes, DOI 10.1214/23-AAP2005;
- Loecherbach, Large deviations for cascades of diffusions arising in oscillating systems of interacting Hawkes processes, DOI 10.1007/S10959-017-0789-6.

Implementation evidence:
- diffusion red: BrownianMotion and OrnsteinUhlenbeck imports absent;
- diffusion green: 6/6 tests;
- full regression after diffusion implementation: 33/33 tests.

The implementation uses caller-supplied innovations so stochastic transitions can be replayed exactly. Internal random sampling is intentionally absent.


Current diffusion closeout classification:
- source/build state: FOUNDATION_V2_1_DIFFUSION_IMPLEMENTED_ON_WORK_BRANCH;
- Brownian/OU implementation: TESTED;
- mathematical model selection matrix: RECORDED;
- internal hostile review: SURVIVES_NARROWED;
- independent review: NOT_PERFORMED;
- main merge: NOT_PERFORMED;
- runtime install/consumption: NOT_ESTABLISHED.


## 2026-10-06 - Poisson / martingale diagnostics

The next high-value mathematical layer from the model-selection review was implemented as diagnostics rather than as another motive generator.

Added:
- homogeneous Poisson null model;
- point-process log likelihood for the null;
- numerical integrated intensity / compensator;
- martingale residual `N - Lambda`;
- target/drive filtering;
- midpoint quadrature around jump discontinuities.

TDD evidence:
- diagnostics red: module absent;
- diagnostics green: 6/6 tests;
- full regression after implementation: 39/39 tests before closeout.

Claim ceiling:
- martingale residuals are calibration evidence across repeated windows;
- one residual does not prove or disprove model correctness;
- diagnostics do not feed directly into motivation.


### Diagnostics continuation

The live branch added a stronger diagnostics contract before closeout:
- time-rescaled compensator intervals between observed events;
- an explicit predictable-jump-boundary regression for integrated Hawkes mass.

After implementation, full regression: 41/41 tests.

The time-rescaling function returns transformed intervals only. V0.4 does not yet perform KS, exponentiality, independence, or other distributional goodness-of-fit tests.

## 2026-10-06 - point-process diagnostic hardening

The next high-value calibration layer was admitted:
- homogeneous Poisson null model;
- numerical compensator integration;
- martingale residuals;
- time-rescaled inter-event intervals.

Provenance note:
- the initial diagnostics implementation and six tests existed only as untracked working-tree material and therefore did not count as durable repository evidence;
- two additional tests established a real missing contract for time-rescaling and predictable-jump integration;
- valid red: import failure for missing time_rescaled_intervals;
- green after implementation: 8/8 diagnostics tests.

Numerical correction:
- compensator integration now uses midpoint quadrature instead of endpoint trapezoidal sampling so event-time jumps are not sampled directly by the integration rule.

Research:
- Brown et al. 2002 time-rescaling theorem, DOI 10.1162/08997660252741149;
- El-Aroui 2025 warning on standard time-rescaling bias for fitted self-exciting models, DOI 10.1080/02664763.2025.2459245;
- Eden-Kramer-Lab/popTRT @ b21a5abcb0f997a8e41c1585065e309dbaa954c4.

No third-party code was copied.


## 2026-10-06 - renewal/refractory temporal extension

The next temporal frontier was implemented as an age-dependent recurrence hazard rather than a full renewal-Hawkes estimator.

Design:
- zero recurrence hazard during an optional absolute refractory interval;
- exponential recovery toward an asymptotic base rate;
- age measured from the most recent matching target/drive event;
- no prior matching event means zero renewal contribution;
- renewal contribution remains separately inspectable from ARIMA baseline, diffusion, and Hawkes excitation.

TDD evidence:
- valid red: `RefractoryRenewalHazard` import absent;
- green focused suite: 9/9 tests;
- full regression after implementation: 50/50 tests.

Research:
- Age Dependent Hawkes Process, arXiv:1806.06370;
- Estimation of the Hawkes Process with Renewal Immigration Using the EM Algorithm, arXiv:1407.7118;
- Renewal Time Points for Hawkes Processes, arXiv:1906.02036.

No public implementation repository of sufficient relevance/quality was admitted for this unit; the implementation is original and paper-guided.

## 2026-10-06 - distributional validation of time-rescaled intervals

The final non-data-dependent diagnostics frontier was implemented.

Contract:
- transform Exp(1) candidate intervals to Uniform(0,1) with `u = 1 - exp(-z)`;
- compute one-sample KS distance against Uniform(0,1);
- report mean and population variance of rescaled intervals;
- report lag-1 correlation only when mathematically defined;
- reject negative or non-finite intervals;
- do not emit p-values or binary model-certification claims.

TDD evidence:
- valid red: `evaluate_time_rescaled_intervals` import absent;
- green focused suite: 8/8 tests;
- full regression after implementation: 58/58 tests.

Research basis remains Brown et al. 2002 time-rescaling plus the recorded 2025 warning about misuse of standard rescaling with fitted self-exciting models.

## 2026-10-06 - Temporal Watch V1 bridge

Live source refresh confirmed `thebrazenbeard/temporal` main at exact head `0fc7071a6b01e609fb2cdc76a32c73276ab27094`, matching the revision already recorded in Volition.

Reviewed exact-head sources:
- `README.md`;
- `temporal.py`;
- `docs/superpowers/specs/2026-09-08-temporal-watch-design.md`.

Integration contract:
- canonical stored UTC timestamp ending in Z;
- stable event ID;
- source and optional refs preserved on MotiveEvent;
- Temporal timestamp converted to relative seconds from explicit canonical anchor;
- duplicate Temporal IDs rejected by MotiveTemporalModel itself;
- batch order reproduces timestamp then stable-ID ordering;
- event text does not infer Volition target or DriveKind.

TDD evidence:
- valid red: `volition.temporal_bridge` module absent;
- focused green: 7/7 Temporal bridge tests;
- full regression after bridge implementation: 65/65 tests.

Temporal remains chronology evidence, not semantic or authority evidence.

Cross-repository verification against the actual Temporal exact-head implementation:
- Temporal 13/13 tests passed;
- actual `append_event` -> `load_events` record fed directly into Volition bridge;
- offset input canonicalized by Temporal to UTC Z;
- Volition relative-time conversion returned exactly 5.0 seconds from the configured anchor;
- duplicate stable ID rejected on re-ingestion.

## 2026-10-06 - Temporal-driven engine currentness clock

V0.8 extends Temporal integration from motive-event chronology to `VolitionEngine` logical time.

Contract:
- `VolitionEngine.elapsed_seconds` is read-only;
- `TemporalClockBridge` maps canonical Temporal UTC timestamps through the existing `TemporalAnchor`;
- engine time advances only by the positive delta to the requested canonical timestamp;
- rewinds fail closed;
- goal adoption/reappraisal timestamps therefore share the same relative chronology as Temporal motive events;
- satiation decay uses the same elapsed-time advancement.

TDD evidence:
- valid red: `TemporalClockBridge` import absent;
- one initial test assertion incorrectly expected new Goal revision 0; source inspection showed the established schema begins at revision 1, so the test was corrected rather than production behavior being altered;
- focused green after correction: 5/5 tests;
- full regression after implementation: 70/70 tests.

V0.8 cross-repository currentness probe:
- Temporal exact-head `append_event` produced canonical records at `2026-10-06T14:00:05Z` and `2026-10-06T14:00:16Z` from offset-aware inputs;
- `TemporalClockBridge` adopted a goal at elapsed `5.0` seconds;
- the second Temporal timestamp advanced the same engine to `16.0` seconds and triggered due reappraisal on the next tick;
- goal revision advanced from established initial revision 1 to revision 2.

## 2026-10-06 - MESO-CRCT non-executable intent bridge

Live source refresh confirmed `thebrazenbeard/meso-crct` exact head `060d0feeb9dc9eb23801082bd8f1c4a7cb06184d`, matching Volition's bound revision.

Reviewed exact-head typed seams include canonical appraisal, arbitration/selection, action tendency, non-executable intent, event identity, and provenance.

Design decision:
- raw perceptual salience, semantic relevance, attention, and pleasure are not imported as Volition desire;
- the bridge consumes only MESO `IntentProposal` shape;
- APPROACH -> OPEN_LOOP MODEL_GENERATED evidence;
- INSPECT -> EPISTEMIC MODEL_GENERATED evidence;
- WITHDRAW -> PROTECTION MODEL_GENERATED evidence;
- HOLD -> no motive signal;
- any effect-authorized or executable input fails closed;
- bridge output does not create Choice or Goal.

TDD evidence:
- valid red: `volition.meso_bridge` absent;
- focused green: 12/12 tests;
- full Volition regression after implementation: 82/82 tests.

Cross-repository evidence:
- MESO exact-head suite: 226/226 tests;
- actual MESO canonical decision cycle generated APPROACH, WITHDRAW, and HOLD IntentProposal objects;
- Volition consumed those exact objects through the bridge;
- approach evidence yielded an eligible Want without creating Choice/Goal;
- protective withdrawal yielded the normal Volition protection veto;
- hold yielded no signal.

## 2026-10-06 - V0.10 historical-currentness adapter

Source refresh: thebrazenbeard/conations @ 51948aac796936f0e7c437722e6f52c883e544e9.
Reviewed README.md, CONATION_WORKSPACE.md, and EVENT_INDEX.md.

Implemented: historical provenance by default; separate fresh-current corroboration; matching target/family requirement; historical magnitude/confidence capped by fresh evidence; terminal lifecycle states rejected for direct reactivation.

TDD: valid red was missing volition.conation_bridge; post-implementation full regression was 104/104 passing.

Free-form source text is not parsed into Volition semantics.

## 2026-10-06 - Pre-Active bounded cognition re-entry bridge

Live refresh retired the previous Volition Pre-Active pin `94cb3b8044d7a4263c50a96bfecfcfebc5533716`. V0.11 binds current `thebrazenbeard/pre-active@a6900dc2d2fb65f4ea66db95fca1b9c5b022450b`, which includes durable observers and temporal initiative models.

Reviewed exact-head contracts:
- `README.md` and `docs/AUTONOMOUS_RUNTIME.md`;
- reserved `pre_active.request_turn` primitive in `src/pre_active/engine.py`;
- same-run autonomous deferral in `src/pre_active/store.py`;
- current Hawkes-threshold initiative policy in `src/pre_active/initiative.py`.

Bridge contract:
- only ENDOGENOUS `CognitionRequest` objects are admitted;
- `effect_authority` must remain false;
- output is a non-dispatching proposal for the reserved re-entry tool;
- arguments contain bounded `reason` and finite non-negative `delay_seconds` only;
- no capability, run/event/request ID, queue priority, or scheduling receipt is manufactured;
- urgency remains descriptive evidence and cannot become authority.

TDD evidence:
- valid red: `volition.preactive_bridge` absent;
- focused green: 13/13 tests.

Cross-repository verification against exact Pre-Active head:
- the exact-head Pre-Active suite completed without failure;
- proposal tool name and arguments matched the actual reserved-tool contract;
- Pre-Active's own parser accepted the arguments unchanged;
- reserved tool capability remained `pre_active.internal.autonomy` and `mutation=False`;
- Pre-Active's own Store moved a durable test run `RUNNING -> WAITING`;
- original capabilities `{files.read, github.read}` remained unchanged;
- autonomous-turn count incremented;
- successor `run.step` retained the same run ID and source `ENDOGENOUS`.

The Pre-Active Hawkes threshold remains a host initiative/wake policy. It is not imported as Volition motive intensity.
