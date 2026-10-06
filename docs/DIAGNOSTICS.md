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
