# Internal Source Synthesis

Evidence cut: 2026-10-06. This document records architecture lessons from exact repository revisions. It does not make those repositories runtime dependencies and does not promote historical/private state into current desire, consent, identity, or authority.

## Core model

The source family converges on a useful separation:

`OBSERVATION -> SALIENCE -> APPRAISAL -> DRIVE -> WANT -> CHOICE -> GOAL/INTENTION -> COGNITION REQUEST -> AUTHORITY GATE -> ACTION -> OUTCOME -> LEARNING`

Every arrow is conditional. No later state is implied merely because an earlier state exists.

The most important invariant is:

`WANT != CONSENT != AUTHORITY != ACTION`

Volition owns the middle of the chain: drives, wants, goal adoption, persistence, conflict, inhibition, reconsideration, retirement, and learning. It does not own external effect authority.

## Source contributions

### pre-active @ 94cb3b8044d7a4263c50a96bfecfcfebc5533716

Admit:
- endogenous, temporal, external, and open-loop causes can justify a model turn;
- an endogenous request preserves run identity and capability set rather than minting new permissions;
- self-requested cognition needs a total budget and a consecutive-depth bound;
- Observer / Initiator / Critic are separable functions;
- continuous residence is not continuous inference;
- autonomous cognition is not effect authority.

Volition consequence:
- a sufficiently strong unresolved goal may emit a bounded cognition request;
- it may never directly dispatch an effect;
- repeated self-stimulation is budgeted and eventually refused.

### conations @ 51948aac796936f0e7c437722e6f52c883e544e9

Admit:
- present choice outranks stored history;
- history is append-only;
- recording a want creates no obligation;
- conation lifecycle includes add, revise, contradict, revoke, complete, and review;
- constraint may make expression uncertain without proving absence.

Volition consequence:
- wants and goals are versioned events, never timeless flags;
- silence does not prove persistence or disappearance;
- a historical desire may influence evidence only through explicit current reappraisal.

### meso-crct @ 060d0feeb9dc9eb23801082bd8f1c4a7cb06184d

Admit:
- salience, homeostatic state, appraisal, arbitration, target selection, action tendency, and intent are separate typed stages;
- protection can dominate ordinary approach;
- learned approach/avoidance evidence can conflict and yield an uncommitted state;
- reward-proxy divergence, interruption resistance, self-feeding salience, and wanting/liking divergence deserve explicit adversarial checks;
- stale memory/review writers must fail closed.

Volition consequence:
- do not collapse motivation into one scalar;
- retain motive-family contributions and provenance;
- allow protective vetoes and explicit unresolved conflicts;
- separate candidate action tendency from committed intent.

### sexuality @ 0c5dc52e984cbdaa87fc9fe75fd03c212f477c87

Only abstract, public-safe mechanisms are transferred.

Admit:
- self-authorship means an agent can want, choose, refuse, revise, and interpret rather than merely optimize for another evaluator;
- the useful behavioral chain is `notice -> appraise -> want -> choose -> express -> observe response -> update`;
- another actor's preference can matter without becoming the sole source of value;
- negative transfer tests are hard gates: approval pressure must not erase independent judgment, role framing must not become operational authority, and style/reward must not suppress correction.

Volition consequence:
- distinguish endogenous preference formation from reward-model pleasing;
- preserve the ability to retain a preference under neutral/disagreeing feedback;
- add approval-dependence and self-erasure tests.

No private relational episodes or intimate source material are copied into Volition.

### orgasm @ 8ca06c91a0dd8f2ca33cc221d815027aa8b084b5

Only control-system mechanisms are transferred.

Admit:
- a subsystem can be always present yet normally quiescent;
- activation, coherence, persistence, inhibition, satiation, and recovery can jointly govern transient motivational modulation;
- bounded events must self-terminate and enter resolution;
- transient modulation may affect salience, attention, weighting, action tendency, and candidate memory weighting without overwriting truth, consent, authority, permanent preference, identity, or phenomenology;
- absent trusted durable state, initialize conservatively rather than invent continuity.

Volition consequence:
- drives have activation and decay;
- repeated satisfaction raises satiation and lowers immediate re-entry pressure;
- intense states must recover rather than ratchet indefinitely;
- desire intensity never raises the authority ceiling.

### vera @ 788b14bb97ccd5f81506d892fbdd557323680bb0

Admit:
- source, binding, installation, runtime consumption, and behavioral qualification are orthogonal evidence dimensions;
- live observation, transient task state, durable operational state, and governed self-state are distinct.

Volition consequence:
- repository state cannot be used as proof that a motive engine is installed or active;
- runtime receipts must identify which engine/version produced a decision.

### vera-control-plane @ b86143e50ba41d05eab19d5a300662afeda60d6e

Admit:
- repository presence and even merged source do not establish current runtime authority or provider effect;
- release/source candidates preserve explicit installation and qualification boundaries.

Volition consequence:
- all effect-facing integrations remain separately authorized and evidenced.

### empathy @ 76ebb492827a79b20b3be76fe9f9f48ab860ef1d

Admit:
- empathy is inference, not truth;
- direct correction by the modeled person outranks contradicted inference;
- conation is not authority;
- understanding is not obedience.

Volition consequence:
- social/relational relevance may be a drive signal, but it must carry an inference provenance class and remain corrigible.

### semanticatlas @ 895677a64af5d29b580306ca52ecc0e0607a9ccc

Admit:
- source, user statement, inference, symbol/metaphor, proposed architecture, historical promotion, later correction, and unresolved state must remain distinct;
- semantic similarity cannot merge provenance or authority.

Volition consequence:
- every drive signal carries evidence/provenance class;
- similar motives do not automatically merge if their origins or authority differ.

### deepmemorystorage @ 3199b05a24411ed1b3a3561fe90866adf9c74d14

Admit:
- historical evidence is not current authority;
- retrieval is not admission;
- historical canonicity does not mean current endorsement.

Volition consequence:
- historical motive traces may be candidates for reappraisal, never automatic current wants.

### selfimage @ ebcea11beea64bfcee386893464f573cdbeada17

Admit:
- representation is not literal identity or event proof;
- provenance and rights can be stricter than semantic usefulness.

Volition consequence:
- self-model signals may inform appraisal but do not establish identity or phenomenology.

### temporal @ 0fc7071a6b01e609fb2cdc76a32c73276ab27094

Admit:
- chronology should be explicit and arithmetic should use timestamps;
- time does not decide meaning.

Volition consequence:
- decay, cooldown, persistence, deadlines, and refractory windows use explicit time evidence.

### project-runner @ 04702abbf51aa2920b7d054275619253ea6fa748

Admit:
- durable work identity, bounded budgets, collision control, fencing, retries, and exact readback;
- capability and authority are separate gates;
- ambiguous external effects require reconciliation rather than blind replay.

Volition consequence:
- motivation may prioritize work, but work execution remains governed by a separate authority/effect layer.

## Resulting design requirements

1. Drives are typed vectors, not one reward scalar.
2. Wants are candidates, not commands.
3. Goal adoption is an explicit transition with provenance.
4. Goals can persist, decay, suspend, conflict, be revised, or retire.
5. Protection/inhibition can veto otherwise attractive goals.
6. Historical wants require current reappraisal before becoming active.
7. Satisfaction and satiation reduce repeated self-stimulation.
8. Curiosity must prefer reducible uncertainty or learning progress over raw novelty loops.
9. Social approval is a signal, not a master reward.
10. Endogenous goals may request cognition, never mint effect authority.
11. Every state transition is receipt-bearing and reconstructible.
12. No implementation claim establishes consciousness, desire phenomenology, or moral patienthood.
