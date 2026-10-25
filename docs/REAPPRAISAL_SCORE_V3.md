# Volition scored reappraisal V3

This version strengthens **structural snapshot consistency**; it does not
establish trusted observation custody, independent review, or an external action
permission.

## Current source contract

1. `VolitionEngine.snapshot()` writes schema `VOLITION_STATE_V3`.
2. Each newly emitted `GOAL_REAPPRAISED` transition now records the finite,
   normalized adopted `score` as canonical float text, alongside `goal_id`,
   `choice_id`, and `revision`.
3. On V3 restore, an active goal at revision 1 must have the original Choice's
   target and adoption score and must not have reappraisal events for the same
   goal. A goal at revision 2 or later requires exactly the contiguous ordered
   revision receipts, with the final time equal to `adopted_at_seconds` and
   the final recorded score equal to its active `adoption_score`.
4. All restored transition details require unique keys and strictly typed
   string pairs; scored reappraisal details have exactly the declared keys.
   Missing, duplicate, untyped, noncanonical, nonfinite, or out-of-range
   reappraisal score text fails closed. An altered active score and an altered
   scored receipt cannot silently disagree.
5. This is an in-memory deterministic engine with no tool dispatch or effect
   authority; all choice/goal/event receipts still have `effect_authority=False`.

## Legacy V2 and migration

Original V2 `GOAL_REAPPRAISED` events recorded revision linkage but no score.
An active goal at revision 2 or higher therefore has an **unrecoverably
unverified revised score from the snapshot alone**. `from_snapshot` rejects that
legacy state explicitly; it does not substitute the original Choice score or
silently manufacture a current reappraisal. A governed consumer must handle
such a snapshot separately and obtain fresh authorized evidence before it
restores any active goal.

Legacy V2 snapshots with no active goal, or with an unrevised active goal whose
score agrees with its Choice, can be loaded. They serialize under V3. Older
unscored historical events about already-ended goals remain historical and do
not qualify a currently active revised goal. Revision downgrade is rejected
when the snapshot still contains matching reappraisal events.

## Qualification ceiling

This contract catches a score changed in only one of the two serialized
locations. A party capable of rewriting both the active goal and its matching
event can still forge internally consistent V3 bytes. Binding a snapshot to a
trusted store, signature/digest, and administered event provenance is a
separate integration requirement. The scored event is **not** proof that the
new appraisal was current, independently measured, or phenomenologically felt.
