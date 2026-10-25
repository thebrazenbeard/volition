# Caller-admitted exact-goal completion V1

Package version: `0.11.0`. State snapshot remains `VOLITION_STATE_V3` because
the existing event representation can carry versioned completion details.

## Purpose

Prevent a late or unverified report about one goal from completing a different
active goal that happens to share a target. Target-only satiation and goal
completion are separate state transitions.

`record_satisfaction(target, amount)` continues to adjust normalized target
satiation and emit `SATISFACTION_RECORDED` with
`admission=unverified_scalar`. It no longer emits `GOAL_COMPLETED` regardless
of amount. A positive scalar does not prove a goal was achieved.

`GoalCompletionClaim` names one outcome event, goal ID, originating choice ID,
positive goal revision, target, result receipt ID, evidence reference,
current-source provenance, and source reference. `GoalCompletionVerifier`
matches a caller-supplied exact-value allowlist and issues
`AdmittedGoalCompletion`. The wrapper cannot be manufactured through its
public constructor without a module-private token. **This is a reference
process-level guard, not independently administered source identity or a
cryptographic security boundary.** A malicious Python caller can still claim
to be a verifier; the hosting system must enforce real observer and custody
authority separately.

`complete_goal(admission)` validates the current active goal's exact ID,
choice, revision, and target, as well as a stable admitted outcome event. A
matched event completes once, emits a non-executable receipt with claim and
verifier references, and clears the active goal. A duplicate identical event
is an idempotent no-op. Conflicting reuse rejects without mutation. The
existing V3 snapshot event ledger reconstructs those outcome IDs on restore.
Restore rejects terminal goal resurrection and duplicate or orphaned
completion receipts; legacy scalar-generated `GOAL_COMPLETED` events are
recognized as historical terminal markers, not converted into admitted
evidence. Legacy `GOAL_SUSPENDED` and `GOAL_REPLACED` receipts lack goal IDs;
restoration associates each with the preceding active adoption in the ordered
event ledger, rejects orphaned receipts, and refuses reactivation of that
historically terminated goal. This establishes local lifecycle consistency
only when the relevant historical event sequence is preserved. The nullable
active goal must match the most recent nonterminal `GOAL_ADOPTED` event exactly;
an active adoption cannot be silently erased. This also rejects
resurrection of a prior goal replaced by direct `adopt_choice()` (which has no
`GOAL_REPLACED` receipt). Persisted snapshots missing an active goal's adoption
history now fail closed rather than guessing the lifecycle.
Reappraisal and completion receipts must also name the goal historically active
at the receipt's position in the ordered event stream; a late receipt for a
superseded goal is rejected even if its old choice and target still exist.

## Exclusions and downstream contract

- Pre-Active `OutcomeCandidate` remains `CANDIDATE` or `REJECTED`; there is no
  adapter automatically turning such a claim into this admission.
- `CURRENT_OBSERVATION` and `CURRENT_STATEMENT` provenance values are typed
  but asserted by the caller. They do not prove an observation occurred.
- An improvement in a MESO need level is not automatically attributable to
  any specific goal. A future trusted adjudicator must bind an action/result
  receipt and verified observed outcome to the exact active goal and choose
  whether completion follows.
- No tool grants, external effect dispatch, verified learning, subjective
  welfare, or phenomenological feeling is implied.
- Protected snapshots still require external integrity/custody. An attacker
  who rewrites both stored state and events can fabricate a self-consistent
  history. `GOAL_SUSPENDED`/`GOAL_REPLACED` legacy receipts do not carry
  exact goal IDs, so their attribution depends on preserved event order; this
  is **not** independently attested lifecycle evidence.
