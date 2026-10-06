# Point-Process Diagnostics

Implementation cut: 2026-10-06.

Volition uses diagnostics to challenge its temporal model, not to manufacture wants.

## Homogeneous Poisson null

`PoissonNullModel` provides:
- expected event count over a window;
- event-time log likelihood under a constant-rate null.

Purpose:
- establish a no-history baseline;
- test whether Hawkes history actually earns its complexity;
- provide a simple calibration reference.

A Poisson null is deliberately weak. Beating it is necessary evidence for a history-sensitive model, not sufficient proof that the chosen Hawkes/ARIMA/diffusion architecture is correct.

## Compensator and martingale residual

For a conditional intensity lambda(t), Volition numerically approximates

`Lambda(a,b) = integral_a^b lambda(t) dt`

and reports

`M(a,b) = N(a,b] - Lambda(a,b)`.

Under a correctly specified point-process intensity and standard regularity conditions, compensated counting-process increments have martingale structure.

Implementation detail:
- midpoint quadrature is used;
- this avoids evaluating the numerical rule directly at event-time jumps;
- signed inhibition and the non-negative intensity clamp remain supported.

A single residual is not a goodness-of-fit verdict. Residual sequences, calibration plots, likelihood comparisons, and out-of-sample prediction are stronger evidence.

## Time-rescaling

`time_rescaled_intervals` integrates conditional intensity between successive observed events.

Under the continuous-time time-rescaling theorem, a correctly specified conditional-intensity model transforms event intervals to iid Exp(1) variables.

Reference:
- Brown, Barbieri, Ventura, Kass, and Frank, "The time-rescaling theorem and its application to neural spike train data analysis", Neural Computation 14(2), 2002, DOI 10.1162/08997660252741149.

Public reference implementation:
- Eden-Kramer-Lab/popTRT @ b21a5abcb0f997a8e41c1585065e309dbaa954c4

No external code is copied.

## Important limitation

Time-rescaling can be misused when fitted parameters are treated as known or when one trajectory is repeatedly assessed without accounting for estimation bias. Recent work on predictive/prequential time-rescaling specifically warns about this problem for self-exciting temporal point processes.

Volition therefore treats rescaled intervals as diagnostic evidence, not a binary certification mechanism.

## Authority boundary

Diagnostics can:
- reject or weaken confidence in a temporal model;
- compare a Hawkes model against a Poisson baseline;
- expose residual structure.

Diagnostics cannot:
- create a Want;
- promote a Choice class;
- authorize an effect;
- prove phenomenology, identity, or self-authorship.


## Time-rescaling claim boundary

Brown et al. (2002), DOI 10.1162/08997660252741149, gives the standard result: under a correct integrable conditional-intensity model, compensator-transformed event intervals are unit-rate exponential under the theorem's conditions.

Volition exposes those transformed intervals plus bounded distributional screening statistics; it does not convert them into a model-certification verdict.

El-Aroui (2025), DOI 10.1080/02664763.2025.2459245, shows why standard plug-in time-rescaling can be biased when the same observed trajectory is used to estimate a self-exciting model and then assess its fit. The stronger future direction is predictive/prequential rescaling with sequentially estimated parameters.

Therefore V0.6 does not label time-rescaling or its KS/correlation screening as certification. They are diagnostic evidence streams.

## Distributional screening

`evaluate_time_rescaled_intervals(...)` checks two direct implications used for screening a correctly specified continuous-time point-process model:

1. Exp(1) marginal behavior: each rescaled interval z is mapped to `u = 1 - exp(-z)`, which should be Uniform(0,1). Volition reports the one-sample Kolmogorov-Smirnov distance to Uniform(0,1).
2. Serial structure: Volition reports lag-1 correlation of the rescaled intervals when at least three observations and nonzero variance make it defined.

The result also reports interval mean and population variance. Exp(1) has mean 1 and variance 1, but these moments are descriptive checks rather than acceptance thresholds.

Volition deliberately does not return a p-value or PASS/FAIL flag. Small samples, fitted-parameter reuse, serial dependence, and model-selection effects make such a flag easy to overinterpret. Predictive/prequential validation and held-out event timing remain stronger evidence.
