# Mathematical Model Selection for Volition

Decision cut: 2026-10-06.

This document classifies the candidate stochastic-process families considered for Volition. "Relevant" does not mean "put everything in the runtime." Each model must earn a specific semantic role.

## Selection rule

A model belongs in the core only if it represents a distinct causal feature of motivation that is not already represented more simply.

Current core temporal decomposition:

`ARIMA expected baseline + optional diffusion deviation + Hawkes event-history effects`

followed by Volition's typed Signal -> Want -> Choice -> Goal pipeline.

## Point-process family

### Poisson process

Classification: REQUIRED NULL / CALIBRATION MODEL.

Role:
- benchmark event arrivals with no history effect;
- test whether Hawkes self-/cross-excitation actually improves fit;
- provide a simple sanity baseline for simulation.

Reason not to use as the motive core:
- ordinary Poisson arrivals do not encode endogenous excitation or inhibition from motive history.

### Cox process

Classification: OPTIONAL STOCHASTIC-BASELINE EXTENSION.

A Cox process has a random intensity process. It becomes attractive if motive-event rate is driven by latent environmental/background variation not adequately represented by deterministic ARIMA plus explicit diffusion.

Important correction:
- Hawkes and Cox processes are related through conditional-intensity modeling, but a standard Hawkes process is not simply identical to a Cox process in the usual construction;
- Hawkes intensity is endogenous to the point process's own event history;
- Cox intensity is modeled as a separate random intensity field/process conditional on which arrivals are Poisson.

Potential Volition use:
- latent stochastic context affecting all motives;
- random baseline intensity shared across targets.

Status: research candidate, not V2 core.

### Self-correcting process

Classification: IMPORTANT ALTERNATIVE / ADVERSARIAL MODEL.

A self-correcting process raises intensity between events and suppresses it after an event. That is useful for phenomena where completing/expressing a motive temporarily makes another occurrence less likely.

Volition already contains:
- satiation;
- inhibitory Hawkes kernels;
- protection vetoes.

Why still keep the model:
- a canonical self-correcting process gives an independent mathematical comparator for whether the current inhibition/satiation architecture captures the intended refractory behavior.

Status: candidate benchmark and possible refractory extension.

### Renewal process

Classification: IMPORTANT REFRACTORY / AGE-DEPENDENT EXTENSION.

A renewal process makes the next-event hazard depend on elapsed time since the previous event through its inter-arrival distribution.

Potential Volition use:
- refractory periods;
- needs that rebuild as time-since-satisfaction increases;
- periodic but non-Poisson re-emergence of motive events.

Relation to Hawkes:
- Hawkes captures event-to-event excitation;
- renewal hazard captures "age since last event" directly;
- modern Hawkes generalizations can use renewal immigration.

Status: likely useful after V2 for satiation/recovery modeling.

## Diffusion and stochastic-process family

### Brownian motion / Wiener process

Classification: IMPLEMENTED OPTIONAL DIFFUSION PRIMITIVE.

Role:
- zero-memory-increment stochastic innovation;
- continuous perturbation around a modeled baseline;
- primitive noise source for richer SDEs.

V2 implementation:
- replayable Brownian state with drift and volatility;
- innovation is caller-supplied, not internally sampled, so exact runs can be reconstructed.

Why not the default motive baseline:
- Brownian variance grows with time;
- it does not mean-revert;
- unconstrained motive pressure would wander arbitrarily far.

### Ornstein-Uhlenbeck process

Classification: IMPLEMENTED PREFERRED DIFFUSION DEFAULT.

OU is Brownian-driven but mean-reverting.

Role:
- transient stochastic variation around a target baseline;
- bounded-in-practice perturbation when long-run mean is meaningful;
- continuous-time analogue of an AR(1)-like restoring process.

V2 uses the exact Gaussian transition for a supplied innovation.

### Geometric Brownian motion

Classification: RESEARCH-ONLY / NOT DEFAULT.

GBM is multiplicative and remains positive, which is useful for stochastic amplitudes or contagion strengths. Published Hawkes work has used geometric Brownian motion for stochastic excitation levels.

Why not default:
- multiplicative dynamics can generate heavy asymmetric growth;
- "motive intensity should always compound multiplicatively" has no current semantic justification.

Possible future use:
- stochastic Hawkes excitation amplitude under a bounded transform.

### General diffusion / SDE models

Classification: EXTENSION FAMILY.

Evidence shows Hawkes systems can be coupled to SDE-driven excitation and can admit diffusion approximations.

Use only when a specific latent continuous state earns its own dynamics. Avoid adding SDEs merely because they are mathematically elegant.

## Markov/state-space family

### Hidden Markov model

Classification: OPTIONAL REGIME MODEL.

Potential use:
- discrete latent regimes such as rested/engaged/depleted or exploration/exploitation modes;
- switching parameter sets for Hawkes or ARIMA components.

Risk:
- hidden regime labels can become reified narratives without enough evidence.

Rule:
- HMM state is operational latent state, not identity, emotion truth, or phenomenology.

### POMDP

Classification: DOWNSTREAM DECISION OPTION, NOT MOTIVATIONAL MEMORY CORE.

POMDP latent dynamics are Markov while belief state can summarize history. Volition does not use that compression as the core representation of motive persistence.

Potential use:
- action selection under partial observability after a Goal exists.

### Markov state-space representation

Classification: COMPUTATIONAL REPRESENTATION, NOT SEMANTIC ERASURE.

ARIMA and exponential-kernel Hawkes can be represented with finite-dimensional state. This can make computation Markovian without implying that the causal history is semantically irrelevant.

Volition requirement:
- compressed state is permitted only when provenance/readback can reconstruct or account for the relevant historical contributions.

### Martingales

Classification: HIGH-VALUE DIAGNOSTIC / INFERENCE TOOL.

For a correctly specified point-process intensity, the compensated counting process

`M(t) = N(t) - integral_0^t lambda(s) ds`

is a martingale under standard conditions.

Volition use:
- residual calibration test for temporal event models;
- detect systematic under/over-prediction;
- compare Poisson/Hawkes variants.

Martingales do not generate wants.

Next engineering candidate:
- compensator and time-rescaling diagnostics, with signed-inhibition/clamped-intensity handling explicit.

## Time-series family

### SARIMA

Classification: LIKELY EXTENSION WHEN SEASONALITY IS EVIDENCED.

Use when motive baselines show repeating cycles that ARIMA cannot parsimoniously represent:
- daily/weekly work rhythms;
- scheduled obligations;
- other verified periodic signals.

Do not invent seasonality without observations.

### ARIMAX / dynamic regression

Classification: HIGH-VALUE EXTENSION.

Adds explicit exogenous predictors to the slow baseline.

Potential signals:
- externally scheduled deadlines;
- resource state;
- verified environment/context measurements.

Boundary:
- exogenous predictors influence forecast; they do not create authority.

### VAR

Classification: PLAUSIBLE MULTIVARIATE SLOW-LAYER EXTENSION.

VAR can model slower linear cross-dependencies among multiple drive baselines.

Relationship to multivariate Hawkes:
- VAR: slower regular-time cross-dependence;
- Hawkes: event-time cross-excitation/inhibition.

This separation is potentially powerful but should be introduced only after enough multivariate observations exist to estimate it.

### GARCH

Classification: CONDITIONAL EXTENSION / NOT CORE.

GARCH models changing conditional variance rather than the mean.

Potential use:
- detect periods where motive-baseline uncertainty/volatility itself changes;
- adapt confidence or exploration budget under heteroskedastic conditions.

Reason not core:
- volatility is not itself desire;
- V2 has no evidence that motivational variance needs a separate autoregressive process.

## Current architecture ranking

CORE NOW:
1. ARIMA baseline.
2. Multivariate Hawkes event history.
3. Explicit inhibition/protection.
4. OU diffusion as optional stochastic deviation.
5. Brownian motion as lower-level diffusion primitive.
6. typed Choice and currentness boundaries.

IMPLEMENTED DIAGNOSTICS:
1. homogeneous Poisson null-model comparison.
2. martingale compensator residuals.
3. time-rescaled inter-event intervals.

NEXT HIGH-VALUE:
1. renewal/refractory hazard.
2. ARIMAX for verified exogenous context.
3. SARIMA if empirical seasonality appears.

CONDITIONAL:
1. VAR for slow cross-drive coupling.
2. HMM/switched Hawkes for evidenced discrete regimes.
3. Cox-process baseline if stochastic latent context is inadequately represented by current diffusion.
4. GARCH if variance dynamics prove informative.
5. GBM for stochastic excitation amplitudes only if data supports multiplicative dynamics.

NOT A CURRENT CORE:
1. POMDP motivational memory.
2. generic Brownian random walk as persistent desire.
3. any model promoted solely because it is mathematically sophisticated.

## Falsification requirement

Every added model must beat a simpler alternative on a named criterion:
- predictive likelihood or calibration;
- residual structure;
- out-of-sample event timing;
- interpretability/provenance;
- safety/currentness behavior.

If it cannot, it does not belong in the production motivational stack.


## Implemented after initial ranking

The following items previously listed under NEXT HIGH-VALUE are now implemented:
- Poisson null-model comparison primitives;
- martingale/compensator residual diagnostics.

Still next:
- time-rescaling transformed inter-arrival diagnostics;
- renewal/refractory hazard;
- ARIMAX when verified exogenous predictors exist;
- SARIMA when empirical seasonality exists.


Time-rescaled compensator intervals are now implemented. The remaining diagnostics frontier is distributional validation of those intervals (for example exponentiality/uniform-transform checks and dependence tests), not interval construction itself.
