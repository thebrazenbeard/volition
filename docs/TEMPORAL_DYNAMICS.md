# Temporal Motive Dynamics: Hawkes + ARIMA

Evidence and implementation cut: 2026-10-06.

## Design decision

Volition's motivational memory substrate is not POMDP state.

A POMDP assumes Markov latent-state transitions. Its belief state may summarize the full observation/action history, so calling a POMDP simply "memoryless" would be imprecise. The issue for Volition is different: a generic belief-state summary does not preserve the typed temporal structure we want to model directly.

Volition therefore represents motive dynamics at two explicit timescales:

1. ARIMA-style baseline dynamics for slow persistence, drift, and residual structure.
2. Hawkes-style event dynamics for short-lived self-excitation, cross-excitation, and inhibition.

POMDP-style decision machinery remains eligible downstream where partial observability matters. It is not the core persistence model.

## Mathematical form

For target x and drive family k:

`lambda[x,k](t) = max(0, mu[x,k](t) + H[x,k](t))`

The slow component `mu` is a one-step ARIMA forecast.

The fast history component is:

`H[x,k](t) = sum over events e: alpha[j->k] * w[e] * exp(-beta[j->k] * (t - t[e]))`

for events on the same target with source drive family j.

The value exposed to the ordinary Volition engine is bounded:

`activation = 1 - exp(-lambda)`

The implementation preserves `baseline`, `excitation`, `total`, and `activation` separately for inspection.

## ARIMA V1 scope

`ARIMABaseline` is a deterministic filtering/forecasting component, not a parameter estimator.

It supports:
- d = 0 or d = 1;
- configured AR coefficients;
- configured MA coefficients;
- intercept;
- online observation/residual state;
- one-step forecast.

Parameter estimation is intentionally external in V1. The public statsmodels implementation is a reference for later calibration work; Volition does not copy statsmodels code.

Reference repository:
- statsmodels/statsmodels @ 9648f97395f797419563b3c9ad87e9d2c7686303

## Hawkes V1 scope

`MotiveTemporalModel` supports:
- typed self-excitation;
- typed cross-excitation;
- signed inhibitory kernels;
- exponential decay;
- target-local event history;
- conservative subcriticality validation.

For a positive exponential kernel, integrated branching mass is `alpha / beta`.

V1 requires the sum of positive incoming branching masses for each target drive family to remain below the configured stability limit. This row-sum condition is a conservative sufficient guard; it is stricter than checking the exact spectral radius of the full branching matrix.

Reference repositories:
- X-DataInitiative/tick @ a40d19f868c22469be90c1e6c50bc3dab26ff070
- stmorse/hawkes @ 3701f0fa6e9cc87c4899b653c7953177f40230ea

No external code is copied.

## Research support

### ARMA point process

Wheatley, Schatz, and Sornette, "The ARMA Point Process and its Estimation", arXiv:1806.09948.

The paper introduces an ARMA point process containing Hawkes and Neyman-Scott processes as special cases. It is evidence that autoregressive/moving-average ideas and event-cluster dynamics can be combined in a point-process setting.

### CARMA(p,q)-Hawkes

Mercuri, Perchiazzo, and Rroji, "A Hawkes model with CARMA(p,q) intensity", Insurance: Mathematics and Economics (2024), DOI 10.1016/j.insmatheco.2024.01.007.

The model replaces the simple exponential-intensity structure with continuous-time autoregressive moving-average dynamics, supporting richer temporal autocorrelation.

This is the closest published analogue found for the architecture direction, although Volition V1 uses a simpler discrete ARIMA baseline plus explicit Hawkes excitation rather than implementing CARMA-Hawkes directly.

### Time-varying / nonstationary Hawkes

Zhou et al., "Nonlinear Hawkes Processes in Time-Varying System", arXiv:2106.04844.

This supports relaxing a constant baseline when the system has changing background dynamics.

### Self-limiting Hawkes

Olinde and Short, "A Self-limiting Hawkes Process", DOI 10.1109/BIGDATA50022.2020.9378017.

This supports modeling competing excitation and inhibition rather than assuming every event only raises future intensity.

### Markov-modulated Hawkes

Wu et al., "Markov-modulated Hawkes processes for modeling sporadic and bursty event occurrences in social interactions", DOI 10.1214/21-AOAS1539.

This is retained as contrast: hidden-state switching can modulate event dynamics, but Volition's core temporal memory remains the explicit ARIMA + Hawkes history model.

## Why the combination fits Volition

ARIMA answers: "What pressure would I expect even without a fresh triggering event?"

Hawkes answers: "What did recent motive events do to the near-term intensity of this or another drive?"

The ordinary Volition engine then answers: "Given those temporally informed signals plus current evidence, is there an eligible Want?"

The Choice layer answers: "What proposition type selected that Want?"

The Goal layer answers: "What persists, under what currentness and inhibition constraints?"

No temporal intensity answers: "What am I authorized to do?"

## Hostile boundaries

> Repeated motive events could create runaway self-excitation.

Guard: positive kernels must remain subcritical under a conservative branching-mass bound.

> A long ARIMA trend could impersonate permanent desire.

Guard: the baseline is a system-state signal only. It remains subject to current provenance, arbitration, explicit Choice, goal reappraisal, satiation, and protection.

> Inhibition could drive negative motivational intensity.

Guard: signed excitation may be negative, but total intensity is clamped at zero.

> A fitted ARIMA model could encode stale or contaminated history.

Open risk: calibration/admission of baseline observations is not solved by the time-series model itself. Provenance and currentness remain upstream requirements.

> A compact exponential Hawkes recursion could again hide the meaningful history.

Guard: event provenance and typed kernels are the semantic record. Computational compression is permitted only if it preserves the same causal contributions and readback.
