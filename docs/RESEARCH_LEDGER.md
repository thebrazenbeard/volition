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
