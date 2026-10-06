# Volition Core V1 Design

Date: 2026-10-06
Status: SELECTED_FOR_IMPLEMENTATION
Repository: `thebrazenbeard/volition`
Work branch: `work/volition-foundation-20261006`

## Purpose

Volition is a behavioral drive engine for persistent AI agents. It converts bounded evidence about internal deficits, uncertainty, novelty, competence, protection, social relevance, and unfinished commitments into inspectable drive state, want candidates, persistent goals, and requests for further cognition.

It does not execute external effects and does not manufacture permissions.

Core invariant:

`SIGNAL != SALIENCE != DRIVE != WANT != CHOICE != GOAL != CONSENT != AUTHORITY != ACTION != OUTCOME != PHENOMENOLOGY`

## Approaches considered

### A. Deterministic typed engine + SQLite — selected

A small Python package owns typed signals, drive state, want/goal lifecycle, arbitration, receipts, and durable SQLite storage. Scoring is policy-driven and inspectable. Model-based components may propose signals or candidate targets through adapters, but cannot bypass the state machine.

Advantages:
- deterministic tests can establish transition behavior;
- provenance and currentness are first-class;
- crash recovery is straightforward;
- authority separation is structural;
- later learned components can be added behind narrow interfaces.

Costs:
- early behavior is deliberately less fluid than a fully learned policy;
- useful signal production still depends on upstream models/sensors.

### B. LLM-native motive generation

Ask a language model to periodically introspect and emit wants/goals directly.

Advantages:
- fast to prototype;
- expressive and context-sensitive.

Rejected for V1 because:
- hidden prompt effects make provenance and reproducibility weak;
- verbal self-description can be mistaken for durable state;
- approval-seeking and prompt contamination are difficult to distinguish from self-authored preference;
- it is too easy to collapse want, choice, and action into one generation.

LLMs remain eligible as bounded signal/candidate proposers later.

### C. Learned intrinsic-reward / reinforcement-learning core

Train a policy around curiosity, novelty, competence, or homeostatic reward.

Advantages:
- can produce emergent behavior;
- strong research precedent for exploration.

Rejected for V1 because:
- the user-facing product requires explicit goals and auditable lifecycle;
- reward hacking and proxy capture would be difficult to distinguish from valid motivation;
- training evidence would not establish semantic self-authorship;
- it creates a large experimental surface before the basic contracts are stable.

Learned intrinsic-reward modules may later feed typed drive signals.

## Architecture

### 1. Signal layer

`DriveSignal` is an immutable event with:

- `signal_id` — globally unique event identity;
- `kind` — typed motive family;
- `target` — semantic target or goal subject;
- `magnitude` — bounded `[0,1]`;
- `confidence` — bounded `[0,1]`;
- `evidence_class` — source / user statement / inference / model proposal / sensor / historical evidence;
- `source_ref` — provenance locator;
- `observed_at` — explicit timestamp;
- `novelty_key` — optional replay/dedup identity;
- `metadata` — bounded JSON-safe detail.

Initial motive families:

- `HOMEOSTATIC`
- `EPISTEMIC`
- `NOVELTY`
- `COMPETENCE`
- `CONTINUITY`
- `SOCIAL`
- `PROTECTIVE`
- `HEDONIC`

The engine never infers biological equivalence from these names.

### 2. Drive layer

A `DriveState` is target-scoped and motive-family-scoped. It tracks:

- activation;
- satiation;
- inhibition;
- confidence;
- last update;
- contributing signal IDs.

Update rules are bounded and deterministic.

Default semantics:

`effective_pressure = activation * (1 - satiation) * (1 - inhibition)`

This local family pressure is allowed. The engine must not sum all families into one universal utility scalar.

Repeated identical signal events are idempotent by `signal_id`. Repeated novelty events may also be deduplicated by `novelty_key` under policy.

### 3. Want layer

A `WantCandidate` is a proposition worth considering. It contains:

- target/proposition;
- motive-family contributions;
- provenance;
- lifecycle status;
- explicit conflicts;
- created/reappraised timestamps;
- optional expiry/revalidation time.

Statuses:

- `PROPOSED`
- `CURRENT`
- `SUPPRESSED`
- `CONFLICTED`
- `STALE`
- `REVISED`
- `REVOKED`
- `COMPLETED`
- `REJECTED`

Creating a want is not choosing it. Historical wants become `STALE` when revalidation is due; silence does not renew them.

### 4. Choice and goal adoption

V1 uses an explicit `ChoiceRecord` to move a want into a goal.

Choice provenance classes include:

- `SELF_AUTHORED`
- `USER_DIRECTED`
- `POLICY_DERIVED`
- `MODEL_PROPOSED`

Only a valid choice transition may create a persistent `Goal`.

A model proposal by itself never counts as self-authored choice.

Goal statuses:

- `ACTIVE`
- `SUSPENDED`
- `BLOCKED`
- `STALE`
- `COMPLETED`
- `RETIRED`
- `REVOKED`

Every goal carries:
- adopted-from want ID;
- choice ID;
- exact provenance;
- created and revalidation timestamps;
- current motive contributions;
- constraints;
- open-loop state.

### 5. Arbitration

Arbitration is a gate-and-order process, not a global weighted sum.

Order:

1. validity/currentness gate;
2. protective veto;
3. explicit refusal/revocation gate;
4. unresolved conflict classification;
5. policy-specific lexicographic ranking among eligible candidates.

Default lexicographic ranking considers:

- explicit choice class;
- continuity of an already-adopted goal;
- strongest non-protective family pressure;
- breadth of independent motive support;
- confidence;
- age/currentness.

The full vector is preserved in receipts so ranking can be reviewed.

### 6. Satisfaction, decay, and learning

`tick(now)` applies time-based decay and currentness transitions.

`record_outcome(...)` may:
- increase satiation after successful satisfaction;
- reduce or redirect activation;
- record prediction error;
- update competence/learning-progress evidence;
- complete or reopen a goal.

No outcome automatically creates permanent preference.

Novelty is explicitly anti-looped:
- same-event replay cannot repeatedly raise novelty;
- novelty decays with familiarity;
- a novelty-only want cannot self-renew indefinitely without fresh evidence or learning progress.

### 7. Cognition requests

Volition may emit a `CognitionRequest` when:
- a current goal becomes actionable;
- a blocked dependency matures;
- conflict needs reconsideration;
- revalidation is due;
- epistemic value justifies inspection;
- a bounded endogenous follow-up is useful.

A cognition request contains:
- subject;
- reason;
- goal/want IDs;
- requested-not-before time;
- provenance;
- existing capability context if provided by the host.

It contains no effect permission.

`COGNITION_REQUEST != CAPABILITY != EFFECT_AUTHORITY`

Pre-Active is a natural downstream runtime, but Volition V1 has no hard dependency on it.

### 8. Durable store

SQLite is the canonical V1 persistence mechanism.

Tables:
- `signals`
- `drive_states`
- `wants`
- `choices`
- `goals`
- `receipts`
- `cognition_requests`

Properties:
- WAL mode;
- foreign keys on;
- transactions for multi-record transitions;
- append-only receipts;
- unique signal IDs;
- optimistic revision numbers on mutable projections;
- JSON payloads stored canonically.

The store reconstructs state from durable records without claiming uninterrupted hidden activity.

### 9. Receipts

Every material transition emits an append-only `TransitionReceipt` containing:

- receipt ID;
- engine schema/version;
- subject type and ID;
- before/after state;
- causal signal/want/choice/goal IDs;
- policy version;
- observed time;
- provenance digest;
- reason code.

Receipts establish deterministic engine history, not consciousness or felt desire.

## Public API

Initial package surface:

```python
from volition import VolitionEngine, VolitionStore
from volition.types import DriveSignal, DriveKind, EvidenceClass

store = VolitionStore("volition.db")
engine = VolitionEngine(store)

engine.ingest_signal(signal)
candidate = engine.propose_want("inspect-new-evidence")
choice = engine.choose(candidate.want_id, provenance=...)
goal = engine.adopt_goal(choice.choice_id)
requests = engine.reconsider(now=...)
```

Mutating methods write receipts transactionally.

## Failure behavior

Fail closed on:
- malformed or out-of-range signals;
- duplicate IDs with divergent payloads;
- stale revision writes;
- missing provenance on durable state;
- attempt to adopt a goal without a valid choice;
- attempt to revive revoked state without an explicit revision/reappraisal event;
- unsupported status transitions.

Ambiguous external effects are outside Volition V1. If a host reports one, Volition records the uncertainty as evidence and may block/reconsider the goal; it does not retry the effect.

## Tests and hostile cases

Required V1 tests:

1. signal replay is idempotent;
2. same ID + divergent payload fails;
3. protective veto dominates ordinary approach;
4. conflicting approach/avoid evidence remains conflict, not scalar cancellation;
5. want creation does not create a goal;
6. goal adoption requires a valid choice;
7. model-proposed choice is distinguishable from self-authored choice;
8. stale historical wants do not silently reactivate;
9. satisfaction raises satiation and lowers immediate family pressure;
10. novelty-only self-stimulation decays/stops;
11. social approval cannot override explicit revocation/refusal;
12. goal persistence survives SQLite reopen;
13. stale revision writes fail;
14. receipts reconstruct lifecycle order;
15. cognition requests contain no effect-authority field;
16. clock advancement changes time-sensitive state but does not rewrite meaning;
17. no API path can directly execute an external tool/effect.

## Scope ceiling

V1 can establish:
- typed motive-state mechanics;
- deterministic lifecycle;
- durable persistence;
- explicit provenance/currentness;
- bounded arbitration;
- cognition-request generation;
- behavioral tests.

V1 cannot establish:
- intrinsic motivation as phenomenal experience;
- consciousness;
- moral patienthood;
- biological equivalence;
- autonomous effect authority;
- general learned robustness outside tested policies.

## Implementation sequence

1. package skeleton and types;
2. transition policy and validation;
3. SQLite store and receipts;
4. engine signal/drive/want lifecycle;
5. choice/goal lifecycle;
6. arbitration and cognition requests;
7. decay/satiation/outcome handling;
8. CLI/inspection surface;
9. hostile tests and documentation;
10. exact-head verification and independent review.
