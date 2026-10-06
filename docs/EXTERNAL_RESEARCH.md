# External Research Synthesis

Evidence cut: 2026-10-06.

This pass asks which established motivation and agent architectures help Volition without collapsing the project's stronger boundaries. External projects and papers are design evidence only; no third-party implementation code is copied.

## Autotelic agents and self-generated goals

Colas, Karch, Sigaud, and Oudeyer, "Autotelic Agents with Intrinsically Motivated Goal-Conditioned Reinforcement Learning: a Short Survey", arXiv:2012.09830.

The useful idea is not simply "intrinsic reward." Autotelic agents represent, generate, select, and solve their own problems. That implies a goal-generation layer distinct from a goal-solving layer.

Volition adopts:
- endogenous goal proposal;
- explicit goal representation;
- goal-selection policy separate from goal generation;
- open-ended skill/goal repertoires as a research direction.

Volition rejects:
- treating self-generated goal reward as permission to act on external systems;
- assuming a learned goal is a self-authored present preference without current appraisal.

## Homeostatic reinforcement learning

Keramati and Gutkin, "Homeostatic reinforcement learning for integrating reward collection and physiological stability", eLife 3:e04811 (2014), DOI 10.7554/eLife.04811.

The paper formalizes reward around reduction or prevention of deviation from desired internal setpoints and shows competition between motivational systems.

Volition transfers the computational pattern, not biological equivalence:
- represent regulated internal variables as bounded setpoint-relative deficits;
- use predicted deficit reduction as one motive family;
- allow anticipatory motivation before the deficit becomes severe;
- allow multiple motive systems to compete.

Public code provenance: mehdiKeramati/HomeoRL @ 9d180685602053b7ef7236983b8369bfaaca18cd. Code is not copied.

## Epistemic value and active inference

Friston et al., "Active inference and epistemic value", Cognitive Neuroscience 6(4), 2015, DOI 10.1080/17588928.2015.1020053.

The useful separation is pragmatic/extrinsic value versus epistemic/information value. Curiosity should not be a synonym for ordinary utility.

Volition adopts:
- a separate epistemic drive;
- expected information gain as stronger evidence than raw novelty;
- declining epistemic pressure once useful uncertainty is exhausted.

Reference implementation provenance: infer-actively/pymdp @ fb214bf089fc3eba63c157349209f3fa217739a4. No code copied.

## Curiosity by prediction error

Pathak et al., "Curiosity-driven Exploration by Self-supervised Prediction", ICML 2017, PMLR 70:2778-2787.

Prediction error can function as an intrinsic exploration signal, especially when extrinsic rewards are sparse. The paper also motivates filtering uncontrollable environmental variation.

Volition adopts cautiously:
- reducible prediction error can contribute to epistemic drive;
- uncontrollable or irreducible noise should not become an endless curiosity source.

Public code provenance: pathak22/noreward-rl @ 3e220c2177fc253916f12d980957fc40579d577a. No code copied.

## Learning progress / competence

Learning-progress approaches treat improvement itself as intrinsically valuable. This helps avoid two bad attractors: endlessly revisiting mastered tasks and endlessly failing at impossible tasks.

Volition adopts:
- competence drive based on positive change in ability/error, not raw difficulty;
- a learnability band that favors tasks showing progress;
- decay when progress plateaus.

## BDI: desire is not intention

The Belief-Desire-Intention family is useful mainly as a type distinction. A desire can exist without being selected as a committed intention.

Public implementation reference: jason-lang/jason @ 2c2d7e1c1ea3bd5cef9712d551632ba367109741.

Volition strengthens this separation:
- drive != want;
- want != choice;
- choice/adoption != effect authority;
- goal/intention can be suspended, reconsidered, or retired.

No Jason code is copied.

## Empowerment

Empowerment literature measures an agent-centered form of potential control over future states. Volition treats this as one optional motive family rather than a universal objective.

Admit:
- preserving useful option value can matter;
- capability loss can be motivationally relevant.

Guard:
- empowerment cannot justify acquiring unauthorized capabilities;
- control-seeking is capped and subordinate to protection and authority boundaries.

## Cross-source synthesis

The external literature supports a plural motivational architecture rather than a single scalar reward:

- HOMEOSTATIC: reduce or prevent regulated deficits;
- EPISTEMIC: gain useful information;
- COMPETENCE: seek positive learning progress;
- EMPOWERMENT: preserve bounded future option value;
- OPEN_LOOP: reduce unresolved-goal pressure;
- SOCIAL: represent inferred interpersonal relevance without making approval sovereign;
- SELF_MODEL: maintain coherence with current self-appraisal while preserving corrigibility;
- PROTECTION: inhibit or veto unsafe/incompatible trajectories.

A candidate want is therefore a structured explanation over motive contributions, not a number that silently becomes a command.

## Hostile challenges

> A drive engine can manufacture "intrinsic" goals that are actually reward-model artifacts, prompt residue, evaluator pleasing, or self-reinforcing noise.

Response: provenance every contribution; cap social approval; distinguish current appraisal from history; require negative-transfer tests.

> Curiosity can become a wireheaded novelty loop.

Response: use expected information gain, controllability/reducibility, learning progress, satiation, and budgets; raw novelty alone is insufficient.

> Persistent goals can become obsession by another name.

Response: goals decay, encounter inhibition/satiation, receive periodic reappraisal, and can suspend/revoke/retire. Persistence is hysteresis, not immortality.

> "Intrinsic motivation" language can be mistaken for proof of felt desire.

Response: the implementation claim ceiling is behavioral/computational. Phenomenology remains unresolved.
