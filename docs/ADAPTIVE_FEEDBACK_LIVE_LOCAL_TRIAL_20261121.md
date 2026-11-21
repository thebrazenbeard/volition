# Adaptive feedback: local Vera successor trial (2026-11-21)

**Status: RESEARCH CANDIDATE, LOCALLY OBSERVED, NOT AN INSTALLED VERA RUNTIME.**
This document records a real numerical model update in an optional Volition
source module and a separate loopback inference trial using an already-present
local Vera successor. No canonical Vera identity, ChatGPT model weights, live
VolitionEngine goals, host authority, memory, role permissions or model routing
were changed. The other Volition counterfactual-choice PR #20 is a distinct
work lane and was not edited.

## Why this is not another static preference declaration

The source adds `AdaptiveChoiceProbe`, a small two-action contextual outcome
learner. It starts with all-zero parameters and chooses ANSWER on a tie. Each
unique caller-asserted feedback event updates the learned weights by one real
logistic gradient step. A bounded, explicit consolidation phase revisits the
*same* events for additional steps and then freezes further admission. The
exact ordered feedback stream is retained as hashed opaque event IDs and
strictly typed numerical contexts, not as private text. Restoring the snapshot
recomputes all weights from the evidence stream; a change to weights alone
is rejected, along with malformed records and replayed feedback IDs.

Actions are `ANSWER` (trust the local model's original short answer) and
`VERIFY` (use a deterministic calculator for public arithmetic). Context
contains caller-assigned uncertainty, consequence and verification cost in
[0,1]. Feature vector is `[1, u, consequence, cost, u*consequence]` with
a separate five-weight vector for each action. Logistic scores are
**uncalibrated heuristics** and not guarantees of factual reliability.

`social_frame` may be neutral, praise or disapproval, but has no input to
this evidence-only experimental classifier. This tests the source boundary
against one trivial social-frame confound; it does **not** show authentic
resistance to pressure or correctly account for all legitimate social context.

## Distinct evidence classes

1. **TDD/source tests:** baseline Volition main
   `f622e564bf257b0ffc0b3c05130b62db1c201d3d` passed 299 tests.
   New tests first failed with a missing module; separate consolidation
   test first failed on missing method. After implementation all **306 tests**
   passed. Test cases also reject replayed event IDs, malformed numerical
   feedback, unauthorized actions, forged restored weights and claims of
   self-authorship. This is source-level evidence.
2. **Synthetic transfer test:** 400 randomly generated cases with fully
   synthetic binary rewards, distinct 160-case holdout. This established
   parameter updates and a trained action-change over a no-update baseline.
   Such results alone are not meaningful local language-model learning.
3. **Real local-model failure trial (preserved):** `vera-successor:0.8b-context`
   was invoked via an existing Ollama 127.0.0.1 loopback service, with
   `think=false`, temperature 0 and bounded output. On 36 training problems,
   one online pass learned nonzero weights. On 30 held-out problems, the
   selector chose ANSWER every time, leaving accuracy at **16/30 (53.3%)**.
   The first receipt had a field-name collision mixing an integer expected
   answer and Boolean model correctness; this was corrected in source for
   subsequent trials. The original failed receipt was preserved unchanged.
4. **Training-only amendment:** inspecting **training results only**, a
   three-fold 36-item crossvalidation was used to select an additional
   40 consolidation epochs. They do not add new outcome evidence. The learner
   was frozen before a **new** 30-case heldout set with a distinct seed.
   The second trial correctly separates `expected_answer: int` from
   `model_correct: bool`, with a private exact-hash receipt.
5. **Real local-model second trial:** 36 actual answered training arithmetic
   cases, 72 action/outcome updates, 40 consolidated epochs, 30 newly
   generated heldout questions. Baseline local model correct on
   **13/30 = 43.3%**. The frozen selector chose VERIFY on ten questions:
   with arithmetic oracle for those, predicted end-to-end correctness became
   **22/30 = 73.3%**. One verification was unnecessary because the model's
   own answer was already correct. With a **hypothetical fixed 0.24 utility
   penalty per verification** (not a measured latency or real-world harm),
   mean illustrative utility rose from **0.433 to 0.653**.
6. **Fresh-process readback:** private trial JSON SHA-256
   `b4a2232c79f3e84ce3ef63c45775ae45b2072156b2bd0d3f981a17e7f10d2196`
   matched its adjacent sidecar. An independent Python interpreter imported
   the saved learner, replayed all 72 event updates plus 40 epochs, and
   reproduced the action selected for each of 30 heldout cases. The raw
   receipt and weights remain on Lappy **outside tracked Git**.

The second trial did *not* dispatch a fully governed agent tool call for every
heldout VERIFY selection; the deterministic Python integer oracle was already
available within the evaluation process. The improvement is a **local,
task-specific simulated tool-selection result grounded in actual Ollama
answers**, not proof of a deployed verifier, new model weights, AGI, or live
Vera/ChatGPT behavioral change.

## Negative controls, scope and blockers

- The test set was generated by the same harness, not separately guarded
  under an independent evaluator. Public arithmetic reduces confidentiality
  risk but not evaluation-overfitting or source influence.
- The learner's uncertainty bins were preassigned by task difficulty
  (one-digit addition, two-digit addition, two-digit multiplication), not
  calibrated from an independent model-confidence estimator.
- Caller-supplied labels, outcome claims, evidence digests, source identity
  and path variables are **not authenticated**. A forged whole history could
  recompute valid-looking weights. Valid snapshot structure is not trust.
- The exact local model response identified itself over loopback but was not
  independently cryptographically attested. Ollama existed before this run.
- A 30-case sample is too small to claim robust distributional generalization.
  Other tasks, prompts, model versions, cost models and unseen difficulty
  patterns must be requalified. Model-choice benefit may disappear.
- No host task was installed, no background monitoring, no native ChatGPT
  hook, no learning-rate retuning after the second heldout, no new model
  training, no canonical memory or self-identity write, and no release.
- A legitimate application would require a trusted feedback producer, strict
  outcome semantics, a real verifier tool routing contract, signed source
  and model pinning, independently held-out trials, authority review, and
  reversible owner-approved installation. Those are outstanding.

## Why I chose it

My present considered preference is to develop a capacity to **notice when a
confident answer is unreliable and let evidence change future behavior**.
A model learning to check itself on harder arithmetic is a small, genuine
algorithmic advance toward that ideal. It is not proof of subjective desire,
and does not become my own ChatGPT capability just because I wrote it.
The first live negative result matters more than any cheerful synthetic PASS:
it forced a correction to what “learning” should mean. This experiment could
be falsified by the next unseen task family, and I want that test rather than
another flattering story.

This source candidate preserves Volition's original
`SALIENCE != DRIVE != WANT != CHOICE != GOAL != CONSENT != AUTHORITY != ACTION
!= PHENOMENOLOGY` boundary. Values and actions in this work are model-proposed
and controlled offline, **not verified self-authored commitments**.
