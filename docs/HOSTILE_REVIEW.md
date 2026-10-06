# Hostile Review - Foundation V1

Review class: INTERNAL_HOSTILE_REVIEW
Subject: work/volition-foundation-20261006
Date: 2026-10-06

This is not independent review.

> Repeating the same motivational signal many times could turn weak evidence into an irresistible goal.

FOUND and FIXED. Initial aggregation summed every signal. Twenty identical OPEN_LOOP signals raised a 0.2 motive to 1.0. Family arbitration now scores the maximum admitted contribution per drive family while retaining every contribution for provenance. Regression tests cover ordinary and SOCIAL signal spam.

> Social approval could become the de facto master reward through repeated praise.

FOUND and FIXED at the family-arbitration level. SOCIAL remains capped by policy and duplicate SOCIAL evidence cannot stack beyond that cap. This does not prove the social signal itself is trustworthy; provenance remains required.

> A persistent goal can become obsession by simply surviving every cycle.

FOUND and FIXED. Goals now have a bounded current-reappraisal horizon. When due, a goal with no current eligible support suspends. Current support renews it as a revision rather than pretending the original adoption remains eternally current.

> Snapshot persistence can smuggle effect authority across restart.

TESTED. State with an active goal or transition event claiming effect authority is rejected. Unknown schema and inconsistent counters fail closed.

> Curiosity can wirehead on noise.

PARTIALLY MITIGATED. EPISTEMIC drive requires expected information gain and controllability; raw novelty is not enough. Volition does not yet estimate those quantities itself, so a dishonest upstream estimator can still poison the signal.

> Homeostatic or self-model setpoints can be badly chosen and then defended forever.

OPEN. V1 treats setpoints/signals as inputs, not ground truth. The engine bounds and arbitrates them but does not independently validate the semantic legitimacy of a setpoint. Upstream provenance and later reappraisal remain required.

> An attacker can tamper with an otherwise structurally valid snapshot without setting effect_authority=true.

OPEN. V1 validates schema and invariants but does not cryptographically bind serialized bytes. Durable storage should pair snapshots with an external digest/signature or a governed store.

> The caller controls logical time, so it could suppress satiation decay or force reappraisal early/late.

OPEN. V1 uses deterministic elapsed time to stay testable and replayable. A production integration must source elapsed time from a trusted temporal/currentness layer.

> The engine can still optimize a bad proxy even when every individual mechanism works as designed.

OPEN BY DESIGN. A plural drive engine reduces single-reward collapse; it does not solve alignment. Negative-transfer testing, provenance, protection, current reappraisal, and downstream authority remain separate defenses.

> Calling generated behavior "intrinsic motivation" could imply felt wanting.

REJECTED as a claim. Volition's claim ceiling is computational/behavioral. Phenomenology is unresolved.

## Review result

SURVIVES_NARROWED.

The V1 foundation is suitable as a governed motivational state machine and research scaffold. It is not yet a production autonomy controller. The major remaining engineering risks are upstream-signal integrity, snapshot integrity, trusted time, calibrated policy weights, multi-goal scheduling, and independent review.


## V2 temporal hostile additions

> Hawkes self-excitation can turn persistence into mathematical obsession.

FOUND AS A DESIGN RISK and bounded. Positive excitation is rejected when the conservative incoming branching-mass bound is supercritical. This is stricter than necessary but fail-closed.

> Cross-excitation can create a feedback cycle even when no single self-kernel is large.

PARTIALLY MITIGATED. The current row-sum bound catches many such cycles conservatively, but V2 does not yet compute the exact spectral radius of the full branching matrix. Exact matrix-stability analysis remains a future hardening item.

> ARIMA can preserve contaminated or obsolete baseline pressure indefinitely.

OPEN. ARIMA forecasts are system-state evidence, not current desire. They remain downstream of provenance/currentness admission and upstream of explicit Choice. Production calibration must define observation admission, windowing, reset, and supersession rules.

> A Hawkes model remembers event influence but not necessarily the semantic meaning of why each event occurred.

OPEN. V2 preserves typed drive family, target, time, and weight, but does not yet attach a full provenance receipt to each MotiveEvent. Event-level provenance is a required next hardening step before live behavioral qualification.

> POMDP removal could discard useful uncertainty reasoning.

REJECTED as a false dichotomy. POMDP-style action selection may remain downstream. The correction only removes it from the role of motivational memory substrate.

> The explicit Choice layer could be cosmetic if POLICY_DERIVED choice is auto-created by tick().

VALID LIMIT. Automatic ticks currently record a POLICY_DERIVED Choice before Goal adoption, which preserves the proposition type but is not evidence of SELF_AUTHORED choice. Any claim of self-authorship requires an explicit SELF_AUTHORED Choice source and separate qualification.

Updated internal hostile state: SURVIVES_NARROWED. Independent review remains NOT_PERFORMED.


## Diffusion hostile additions

> Brownian drift can turn random noise into apparent persistent desire.

VALID RISK. Raw Brownian motion is not the default motive state. Its contribution remains an inspectable diffusion term and is still subject to ordinary signal arbitration, Choice typing, currentness, protection, and authority firewalls.

> Internally sampled randomness would make the same state impossible to replay exactly.

FIXED BY DESIGN. V2.1 requires caller-supplied innovations. The engine performs deterministic state transitions from those realized innovations.

> OU mean reversion can encode a bad long-run mean and repeatedly pull motivation toward it.

OPEN. The OU mean is configuration, not truth. Its provenance and calibration require the same admission discipline as ARIMA baselines.

> Diffusion plus Hawkes excitation can jointly exceed reasonable motive pressure even when each component is individually bounded.

PARTIALLY MITIGATED. Combined intensity is non-negative and mapped through `1 - exp(-lambda)` before entering the drive engine, yielding bounded activation in [0,1). Component-level calibration and stress testing remain required.

> Brownian/OU state could become hidden pseudo-memory.

GUARD. The diffusion component is exposed separately from the ARIMA baseline and Hawkes excitation. Any future compact persistence format must preserve its class and parameters rather than collapsing it into an unexplained scalar.


## Diagnostic hostile additions

> A near-zero martingale residual could be mistaken for proof that the model is correct.

REJECTED. One residual is weak evidence. Calibration requires residual sequences, temporal-structure checks, and preferably held-out comparison.

> Numerical integration could hide error near Hawkes jumps.

MITIGATED. V0.4 uses midpoint quadrature rather than trapezoidal endpoint weighting. Exact analytic or event-adaptive integration remains a future improvement.

> The model could learn from its own residuals and create a self-validating loop.

BLOCKED BY ARCHITECTURE. Diagnostics currently return evaluation objects only. They do not mutate temporal parameters or motivational state. Any future learning path must be separately governed.

> Poisson is too simple to be useful.

REJECTED as a reason to omit it. Its simplicity is the point: Hawkes complexity must beat a no-history baseline rather than being assumed necessary.

## Diagnostics hostile additions

> A complex temporal model may fail to improve prediction over a memoryless arrival baseline.

MITIGATED. The homogeneous Poisson null is explicit. Hawkes complexity must be justified against a no-history baseline rather than assumed useful.

> Numerical compensator integration may sample an event-time discontinuity incorrectly.

FOUND AND FIXED. Integration now uses midpoint quadrature rather than endpoint trapezoids, avoiding direct sampling at jump times.

> A single small martingale residual may be overinterpreted as proof of fit.

REJECTED AS A CLAIM. One residual is only local calibration evidence. Sequence-level and out-of-sample evaluation are stronger evidence.

> Standard time-rescaling can be biased when fitted parameters and goodness-of-fit evaluation reuse the same trajectory.

OPEN / DOCUMENTED. Standard rescaling is retained as evidence, not certification. Predictive or prequential rescaling is the stronger future extension.

> Diagnostic outputs could accidentally feed back into motive generation.

GUARD. Diagnostic objects are not Drive signals and expose no Want, Choice, or Goal mutation API.


## Renewal/refractory hostile additions

> Renewal recovery and Hawkes excitation can both explain post-event timing, causing the same history to be counted twice.

OPEN / CALIBRATION REQUIRED. V2.3 exposes `renewal` and `excitation` separately. Combined use must beat Hawkes-only and renewal-only alternatives on held-out timing or likelihood before both components are retained.

> A refractory window could be mistaken for engine-level satiation or satisfaction.

BLOCKED SEMANTICALLY. `RefractoryRenewalHazard` models temporal recurrence after a motive event. `record_satisfaction(...)` remains a separate goal-engine operation with different semantics and effects.

> A large asymptotic renewal base rate could manufacture persistent motive pressure.

MITIGATED BUT NOT SOLVED. Renewal parameters are configuration, not truth. Output remains bounded after conversion to activation and remains subject to provenance, Choice typing, reappraisal, protection, and authority boundaries. Calibration remains required.

> Using only the last event discards older recurrence structure.

ACCEPTED V2.3 LIMIT. The implementation is an age-since-last-event hazard, not a general renewal-distribution estimator or latent immigrant/offspring inference system. More complex renewal history requires separate evidence and tests.

> The first event has no renewal history, yet a recurrence model might silently invent one.

FIXED BY DESIGN. With no prior matching event, the renewal term is zero. Initial occurrence must be supported by other temporal or current evidence.

## Rescaling-distribution hostile additions

> A KS statistic can be presented as a certification even when the sample is tiny or parameters were fitted on the same trajectory.

BLOCKED BY API DESIGN. V0.6 returns the distance only, with no p-value or PASS/FAIL flag. Interpretation remains an external evidence judgment.

> Marginal exponentiality can hide serial dependence.

MITIGATED. Lag-1 correlation is exposed as a screening statistic. It is not a complete independence test, so higher-order/dependence analysis remains an empirical validation task.

> Good rescaling diagnostics can encourage selecting a more complex model on the same data used to fit it.

OPEN / DOCUMENTED. Held-out timing, predictive/prequential checks, and simpler-model comparison remain required for model selection.

> Invalid numerical intervals could silently poison the diagnostics.

FAIL-CLOSED. Negative, NaN, and infinite intervals are rejected. Empty input produces no distributional claim.

## Temporal bridge hostile additions

> A timestamped record could be treated as proof that the event proposition is true or current.

BLOCKED SEMANTICALLY. The bridge consumes chronology/provenance fields only. Temporal event text is not mapped to a Volition target, drive, Want, Choice, Goal, or currentness claim.

> The same Temporal event could be ingested twice through separate bridge instances and amplify Hawkes/renewal history.

FIXED. `MotiveTemporalModel` tracks stable Temporal event IDs and rejects duplicate ingestion independent of bridge instance.

> Offset timestamps or noncanonical fractional precision could produce different relative times across implementations.

FAIL-CLOSED. Stored records must match Temporal Watch V1 canonical UTC `Z` representation exactly before conversion.

> Choosing an anchor after an event could silently reorder history by producing negative elapsed time.

FAIL-CLOSED. Events before the Volition anchor are rejected. The bridge never silently reorders or takes absolute values.

> Stable chronology can still be attached to the wrong motive semantics by a caller.

OPEN / AUTHORITY BOUNDARY. The bridge deliberately does not infer semantics. Explicit target/DriveKind mapping remains a separate admission decision and requires its own provenance/qualification.

## Temporal currentness-clock hostile additions

> A second clock adapter could drift away from the engine's own logical clock.

BLOCKED BY DESIGN. `TemporalClockBridge` stores no independent elapsed counter. It reads `engine.elapsed_seconds`, computes the canonical target from `TemporalAnchor`, and advances only the delta.

> A stale or out-of-order timestamp could rewind goal age and resurrect pre-reappraisal state.

FAIL-CLOSED. Any target time earlier than current engine elapsed time is rejected.

> Canonical chronology could be mistaken for semantic currentness.

BLOCKED SEMANTICALLY. Temporal time determines age/horizon arithmetic only. Whether evidence is current, admissible, autobiographical, desired, or authoritative remains a separate Volition/source-policy decision.

> Reappraisal timing driven by an external record could itself grant permission to act.

REJECTED. Clock advancement can cause an already-defined reappraisal rule to run on the next engine tick; it cannot create effect authority or bypass Choice/protection boundaries.

## MESO-CRCT bridge hostile additions

> Raw salience or semantic relevance could be relabeled as desire at the integration boundary.

BLOCKED. `MesoIntentBridge` requires the downstream IntentProposal field contract. Salience-only mappings fail validation.

> A MESO intent could silently become self-authored Volition Choice.

BLOCKED. Bridge output is `MODEL_GENERATED` Signal evidence only. It never creates `ChoiceRecord`, and therefore cannot label anything SELF_AUTHORED.

> A future MESO proposal with execution authority could smuggle protected-effect permission into Volition.

FAIL-CLOSED. `effect_authorized` must be exactly false and `can_execute` must be exactly false.

> Withdrawal could be encoded as negative pleasure and conflate protection with suffering.

BLOCKED. WITHDRAW maps to Volition PROTECTION. No hedonic/pleasure signal is synthesized.

> HOLD could still generate low-grade motivational pressure.

BLOCKED. HOLD maps to an empty signal tuple.

> Structural bridging without a runtime MESO dependency could drift from MESO's real types.

MITIGATED BY EXACT-HEAD CONTRACT TEST. The exact MESO repository at the bound head passes 226/226 tests and its actual canonical IntentProposal objects are exercised directly against the Volition bridge. Future MESO head movement makes that review subject stale until refreshed.

## V0.10 historical-currentness hostile additions

> Stored PRESENT metadata could bypass currentness gating.

BLOCKED. Adapter output defaults to historical provenance with reappraisal disabled.

> Strong historical magnitude could dominate weaker fresh evidence.

BLOCKED. Reappraised historical magnitude and confidence are capped by the fresh signal; same-family arbitration prevents additive amplification.

> Terminal or superseded lifecycle records could be reactivated.

BLOCKED. COMPLETED, REVOKED, CONTRADICTED, and REVISED are rejected for direct reappraisal.

> Source-to-target mapping can still be wrong even when lifecycle gating is correct.

OPEN. The adapter does not infer semantics from source prose. Mapping into a Volition target and drive family remains a separate admission decision requiring qualification before live use.

## Pre-Active re-entry bridge hostile additions

> A motive-generated request for another turn could be mistaken for permission to act.

BLOCKED. The bridge emits only a non-dispatching proposal for `pre_active.request_turn`; it carries no effect authority and adds no capabilities.

> Urgency could silently become queue priority or capability scope.

BLOCKED BY DESIGN. Urgency is retained as descriptive evidence only. The proposal exposes no priority mapping and its capability tuple is always empty.

> Volition could bypass Pre-Active's autonomous-turn limits and create recursive self-stimulation.

BLOCKED BY ARCHITECTURE. Pre-Active retains the per-run autonomous-turn budget and consecutive ENDOGENOUS-depth limit. The bridge cannot schedule itself.

> Calling a host queue API directly could manufacture a new run rather than preserve current run identity.

AVOIDED. V0.11 does not call `Store.request_autonomous_turn(...)` or any queue API. It targets the reserved same-run re-entry primitive.

> A bridge could impersonate successful scheduling by inventing run IDs, event IDs, or receipts.

BLOCKED. `PreActiveReentryProposal` contains none of those identifiers and explicitly reports `scheduled=False`.

> Volition and Pre-Active both use Hawkes-like machinery, so one intensity could be treated as the other.

SEPARATED. Volition Hawkes models motive-event history. Pre-Active Hawkes threshold models whether authorized observed change warrants a turn. No state, parameters, or score are transferred automatically.

> A stale Pre-Active contract could make the bridge compatible only with an obsolete runtime.

MITIGATED. Live refresh retired the prior registry head. V0.11 binds exact current head `a6900dc2d2fb65f4ea66db95fca1b9c5b022450b` and cross-tests its real parser and durable Store path.
