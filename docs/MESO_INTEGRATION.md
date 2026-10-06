# MESO-CRCT Integration

Implementation cut: 2026-10-06.

Bound source:
- repository: `thebrazenbeard/meso-crct`
- exact head: `060d0feeb9dc9eb23801082bd8f1c4a7cb06184d`
- exact-head contract reviewed: typed appraisal, arbitration/selection, action tendency, non-executable intent, event identity, and provenance modules.

## Integration seam

Volition does not consume raw MESO perceptual salience, semantic relevance, attentional priority, pleasure, or arbitrary circuit state as desire.

The bridge consumes only MESO's downstream `IntentProposal` contract, which is created by MESO's typed decision-cycle path and explicitly carries:
- target ID or no target;
- intent kind: `approach`, `inspect`, `withdraw`, or `hold`;
- bounded strength;
- source tendency and source;
- `effect_authorized=False`;
- `can_execute=False`.

## Mapping

`APPROACH` -> one Volition `OPEN_LOOP` signal.

`INSPECT` -> one Volition `EPISTEMIC` signal whose transformed value preserves MESO intent strength.

`WITHDRAW` -> one Volition `PROTECTION` signal. Withdrawal is not encoded as negative pleasure.

`HOLD` -> no Volition motive signal.

All emitted signals use `ProvenanceClass.MODEL_GENERATED` and a source string that preserves MESO intent kind, source tendency, and source.

## Authority and proposition fidelity

A MESO IntentProposal is a non-executable proposal, not a Volition Choice.

`MesoIntentBridge` therefore:
- never creates `ChoiceRecord`;
- never creates or adopts a Goal;
- never labels evidence SELF_AUTHORED;
- never grants effect authority;
- rejects an intent if `effect_authorized` is not exactly false;
- rejects an intent if `can_execute` is not exactly false.

A caller may later evaluate the generated signals in Volition. Any subsequent Choice must still be typed through Volition's own Choice boundary.

## Salience firewall

The adapter intentionally rejects raw salience-shaped mappings. This preserves MESO's invariant:

`salient != authorized`

and Volition's related separation:

`SALIENCE != DRIVE != WANT != CHOICE != AUTHORITY`

Perceptual salience and semantic relevance can affect MESO's own typed appraisal/selection path, but cannot bypass that path by being injected into Volition as desire.

## Dependency choice

Volition does not require MESO-CRCT as a runtime package dependency. The bridge accepts the structural fields of the exact `IntentProposal` contract and binds MESO's exact source head in `docs/SOURCE_REGISTRY.yaml`.

This keeps the Volition wheel standalone while allowing exact cross-repository compatibility tests against a checkout of MESO-CRCT.

## Cross-repository verification

At MESO exact head `060d0feeb9dc9eb23801082bd8f1c4a7cb06184d`:
- MESO suite: 226/226 tests passed;
- canonical `build_target_appraisal` + `run_decision_cycle` produced real `APPROACH`, `WITHDRAW`, and `HOLD` IntentProposal objects;
- Volition mapped APPROACH to OPEN_LOOP MODEL_GENERATED evidence;
- Volition mapped WITHDRAW to PROTECTION and the normal protection veto applied;
- Volition mapped HOLD to no signal;
- evaluating approach evidence created a Want but did not create a Choice or Goal.

## Claim boundary

This integration establishes a tested computational contract between two repositories. It does not establish subjective wanting, self-authorship, consent, biological equivalence, runtime installation, or permission to execute effects.
