# Renewal and Refractory Dynamics

Implementation cut: 2026-10-06.

## Purpose

Volition V2.3 adds an optional age-dependent recurrence hazard for motive-event streams.

This solves a different problem from Hawkes excitation:
- Hawkes asks how prior events transiently excite or inhibit future intensity;
- renewal/refractory hazard asks how event probability changes as time passes since the last matching event.

The two terms remain separately inspectable.

## Implemented hazard

`RefractoryRenewalHazard` uses:
- `base_rate`: asymptotic recurrence hazard;
- `refractory_seconds`: absolute zero-hazard interval after a matching event;
- `recovery_rate`: exponential recovery speed after the refractory interval.

For event age a:

`R(a) = 0` for `a <= refractory_seconds`

`R(a) = base_rate * (1 - exp(-recovery_rate * (a - refractory_seconds)))` otherwise.

This nonnegative age-dependent hazard defines a valid waiting-time model. It is intentionally narrower than a general renewal-distribution framework.

## Temporal decomposition

For target x and drive family k, the current temporal model is:

`lambda[x,k](t) = max(0, mu_ARIMA[x,k](t) + D[x,k](t) + R[x,k](age) + H[x,k](t))`

where:
- `mu_ARIMA` is slow expected baseline pressure;
- `D` is optional Brownian/OU stochastic deviation;
- `R(age)` is optional recurrence/refractory recovery;
- `H` is Hawkes self-/cross-excitation or inhibition.

If no prior matching target/drive event exists, the renewal contribution is zero. First occurrence therefore still comes from baseline, diffusion, or cross-process evidence rather than an invented recurrence history.

## Why this is not full renewal Hawkes

Published renewal-Hawkes work can replace Poisson immigration with a general renewal process and infer latent immigrant/offspring structure.

Volition V2.3 does not implement that estimator.

It implements the smaller semantic unit needed here: explicit age-since-last-event recurrence/refractory behavior.

Research support:
- Raad, Ditlevsen, and Loecherbach, `Age Dependent Hawkes Process`, arXiv:1806.06370. Age allows post-jump recovery/refractory behavior inside a Hawkes framework.
- Wheatley, Filimonov, and Sornette, `Estimation of the Hawkes Process with Renewal Immigration Using the EM Algorithm`, arXiv:1407.7118. Renewal immigration separates non-Poisson baseline recurrence from Hawkes offspring excitation.
- Raad, `Renewal Time Points for Hawkes Processes`, arXiv:1906.02036. Renewal structure can coexist with ordinary and age-dependent Hawkes processes.

## Semantic boundaries

Renewal recurrence is not engine-level satisfaction.

`record_satisfaction(...)` in the goal engine changes satiation and may complete a Goal. `RefractoryRenewalHazard` only models event recurrence as a function of age since the last matching temporal event.

Likewise:
- recurrence hazard does not create effect authority;
- an age-dependent signal is still SYSTEM_STATE evidence;
- recurrence does not imply phenomenological wanting;
- recurrence does not promote MODEL_PROPOSED or POLICY_DERIVED Choice to SELF_AUTHORED.

## Calibration boundary

Using Hawkes excitation and renewal recovery on the same event stream can double-count temporal structure if both are fitted carelessly.

Required future calibration:
- compare against Poisson and Hawkes-only baselines;
- evaluate held-out likelihood/event timing;
- inspect martingale/time-rescaling diagnostics;
- prefer the simpler model when renewal adds no measurable value.
