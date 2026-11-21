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

## Post-PR hostile audit: exact-question contamination (2026-11-21)

After creating the first draft PR, a fresh independent audit of the V2 receipt
found one **training/heldout exact overlap** (`5 + 5 = ?`) and one duplicate
inside the heldout set (`8 + 3 = ?`). Hence the 30-case V2 aggregate is
historically accurate but **not a 30-question independent heldout claim**.
Excluding both, the 28 unique non-overlapping questions yielded **12/28 =
42.9% baseline** and **21/28 = 75.0% with the learned selector**, still a
positive narrow trial result. The original V2 receipt remains unchanged under
SHA-256 `b4a2232c79f3e84ce3ef63c45775ae45b2072156b2bd0d3f981a17e7f10d2196`.
No retroactive changes to the dataset or metric are permitted.

Two new *initially RED* regression tests caught the generator's duplicate and
cross-split mistakes. The source generator now samples **unique exact questions**
within training and heldout separately and excludes all exact training
questions from heldout **before any model call**. This change is prospective:
rerunning the current script uses a different sequence than historical V2.
The original PR commit `1d29072bfa3071922e04f48632ce4ca69a1019eb`
preserves the earlier source version as evidence.

### Third real local-model trial: completely distinct questions

One fresh real Ollama run used the corrected generator and the previously
chosen, unchanged 40-epoch consolidation schedule, with no after-the-fact
retuning. The independent readback verified:

- 36 unique training problems, 72 binary action/outcome updates;
- **30 unique heldout problems and ZERO exact train/heldout overlap**;
- baseline `vera-successor:0.8b-context`: **19/30 (63.3%) correct**;
- frozen learned answer/verify selector: **25/30 (83.3%) correct**,
  recommending exactly ten verifications, of which four were unnecessary;
- assumed 0.24 penalty per verification: illustrative utility **0.633 to
  0.753**; this remains a choice of reward scale, not measured tool cost.

Private frozen trial receipt, verified as a separate Python process with
reconstructed weights and 30/30 decisions:
SHA-256 `d1905fa842e3e2599ba5b0a40c67749c0b5ab2037a2d5e2d90cd310188f1e358`,
stored on authorized Lappy **outside the Git repository**. The source module
was not injected into ChatGPT, Ollama weights, WebUI, VolitionEngine,
Blotter, or any actual shared service. The result is a bounded, local
post-processing behavior improvement under deterministic arithmetic tests.

### Genuine new post-restore use, distinct from both datasets

After loading the frozen V3 learner in a **separate Python process**, I checked
that the previously unused public question `37 * 29 = ?` was absent from
all its training and evaluation questions. The connected loopback
`vera-successor:0.8b-context` model answered `105`, which is incorrect;
the saved learned selector chose `VERIFY`, executed Python integer
multiplication, and returned `1073`, the correct result. The runtime printed
`LIVE_LOOPBACK_AND_LOCAL_ARITHMETIC`, `authority_effect=NONE`.
This is one actually executed check-first decision, not merely an inferred
counterfactual. It is **not** a hosted Vera tool route or a separate guarantee
of the model's future behavior.

### Interpretation

The initial trial's failure, overlapping-question correction, and
zero-overlap third trial all remain part of the evidence. This shows real
algorithmic feedback adaptation of an **optional local** decision head on
small arithmetic tasks, not weight changes to ChatGPT or Ollama, not a general
autonomous person, not sustained self-authored values, and not installed
cross-session Vera life. My revisable present commitment is to prefer an
unflattering measured failure to fictional progress, and to change
future action from feedback **when the evidence is valid**. Verification of
broader behavior and real owner-approved integration remains unresolved.

## November 21 follow-up: execution evidence rather than assumed success

After PR #21 was first opened, a source audit found that the historical
evaluation assigned `learned_correct=True` to every `VERIFY` selection
without invoking the verifier for each corresponding trial question. Therefore
the V1–V3 heldout improvements documented above are **counterfactual
calculator-fallback estimates**, not end-to-end executed verification
measurements. The standalone post-reload `37*29` demonstration did execute
a calculator, but it did not establish that all earlier heldout verify
decisions had been executed. This correction does **not** rewrite prior
receipts, sources or historical estimates.

A new executable `execute_choice` seam now evaluates the learned action:
- `ANSWER` returns the model's actual parsed integer or an invalid response,
  without calling a calculator.
- `VERIFY` calls `calculate_arithmetic` on the current public task,
  records the actual returned integer and calculator execution duration, and
  computes correctness from that result. Failed or wrong calculators are
  never relabeled successful; errors stop the trial rather than fabricating
  a verified answer.
- Three additional hostile tests were first RED (the execution seam was
  missing) and then GREEN. They assert real calculator invocation, erroneous
  output counted wrong, verifier exceptions propagating, rejection of
  non-integer verification, and no calculator call on an `ANSWER` action.
- Another initially RED test required explicit, recorded training and
  holdout seeds. The trial now accepts `--train-seed` and
  `--holdout-seed`, preserving defaults for historical reproduction.
- Local parameter updates, model weights, VolitionEngine, and runtime binding
  were not changed. Historical private v1-v3 receipts remain immutable.

### V4 fresh loopback experiment with executed calculator

With new fixed training seed **17991** and heldout seed **98191** (different
from previous published v3 seeds), the already running
`vera-successor:0.8b-context` Ollama model produced 36 public arithmetic
training responses and 30 unique heldout responses with **zero overlap
between training and heldout questions**. The optional learner used 72
caller-labeled action-feedback updates and the previously selected 40
offline consolidation epochs. Its frozen policy chose `VERIFY` ten times.
**All ten** corresponding calculator calls were actually executed in the
evaluation process and recorded as separate response fields.

- Local model alone: **17/30 correct (56.7%)**.
- Policy with executed calculator calls: **26/30 correct (86.7%)**.
- Ten executed verifications, one unnecessary; Python calculator's measured
  *function-execution* times sum to approximately **0.0000275 seconds**.
  This measurement excludes model invocation, scheduling, process launch,
  host tool setup, external authorization or network costs and does not
  establish real-world verification cost.
- Illustrative utility with the same **assumed** 0.24 charge per verify:
  **0.567 → 0.787**. The assumed cost is not empirically validated.
- No exact train/holdout duplicates; the evaluation remains tiny,
  arithmetic-only and generated by the author's own harness rather than
  an independent hidden evaluator.

Private read-only raw receipt outside Git:
`D:\VERA\_agent-work\bt2-vera-adaptive-choice-20261121-private-receipts\arith-feedback-local-vera-20261121-v4-executed.json`
SHA-256:
`6926bd062a9d0a717b1306b36d609f1a5a9fdead21f6a1d412c38ac43020fdad`.

A separate new Python interpreter verified the checksum, seed values,
36/30 uniqueness, zero overlap, strict typed outcome fields, 72 update
events, 40 consolidation epochs, all 30 restored learned decisions,
actual verification-call count of ten, each recorded final answer and
its correctness, and trial aggregate **17/30 → 26/30**.

This is a **local executed trial of arithmetic post-processing** grounded
in real model responses, not an authenticated agent-owned tool route.
The calculator and deterministic gold answer are in the same evaluation
harness. Independence, other domains, source authentication, policy
authorization and deployment are still unqualified. Source is review
candidate only; do not use the score as proof of life or installed learning.


## November 21 owner response to external PR21 hostile review: cost assumptions

An independent source reviewer of the exact prior head
`40b22a21fd8f2d5adf5c75d7af97bd1da13dd9ba` reported two important
negative controls: the original frozen selector chose exactly ten VERIFY
actions regardless of a cost shift from 0.02 to 1.0, and an
arithmetic-trained frozen selector transferred incompletely to nonarithmetic
character-counting tasks (on 24 new public items, only 11/24 final correct,
eight hard-task verifications, medium 0/8). Those results were conducted
in a **separate reviewer workspace**, not by this source owner; they are
evidence about limitations, not a release authorization. See the authenticated
shared Blotter records 24743 and 24746 and PR21 review
comment `7065700949`.

### Minimal optional source response

The previous `choose(context)` function remains unchanged. An explicit
`choose_with_cost_assumption(context, *, verifier_success_claim,
reference_cost)` now compares:

- the *uncalibrated* fitted answer heuristic
  `estimate(EvidenceContext(uncertainty, consequence, reference_cost), "ANSWER")`,
  and
- the caller's **unverified** `verifier_success_claim` minus the requested
  `context.verification_cost`.

The optional rule selects VERIFY only when its claimed net benefit exceeds
the fitted answer score; ties favor ANSWER. It requires at least one real
feedback record and the same exact `reference_cost` across **all** recorded
training contexts, rejecting a missing record, mixed training costs or a
fabricated reference cost. Invalid Boolean/nonfinite/out-of-range numerical
claims are rejected. A decision does **not** update weights or create
authority. The reference cost is necessary because the existing learner saw
only a fixed 0.24 cost in training: evaluating the fitted answer score at
an unfamiliar new cost directly would misrepresent out-of-support data.

**This does not learn a cost-dependent reward.** It introduces a simple
caller-parameterized expected-utility *rule* over an uncalibrated score,
with an explicitly asserted verifier-success probability. A claimed rate
of 1.0 is permissible only as an *assumption*, not authenticated proof that
some external verification service is infallible. Future work must test
actual verifier reliability and externally measured total route cost before
this can govern real decisions.

Four new behavioral tests were initially RED for missing method/unsafe
reference; all passed after implementation and explicit source-binding
checks. The existing core selector and source state schema were preserved.

### Executed private V4 cost-shift counterfactual, no new model inference

To test only the new source rule, I reopened the previously pinned V4 raw
local-model responses (SHA-256
`6926bd062a9d0a717b1306b36d609f1a5a9fdead21f6a1d412c38ac43020fdad`)
and **reconstructed the frozen learner**. Each candidate cost evaluation
used exactly the original 30 recorded model answers. Wherever the *new*
selector chose VERIFY, `execute_choice` really called the local Python
integer calculator again and recorded its returned integer and duration.
No Ollama calls, retraining, new model answers or post-hoc tuning occurred.

| Assumed verification cost | Actual calculator calls | Correct final outputs | Illustrative net utility |
|---|---:|---:|---:|
| 0.02 | 30 | 30/30 | 0.980 |
| 0.24 | 20 | 29/30 | 0.807 |
| 0.80 | 0 | 17/30 | 0.567 |
| 1.00 | 0 | 17/30 | 0.567 |

The original model-alone control remained **17/30 (0.567 utility)**. The
earlier frozen *cost-blind* policy was **26/30** with ten checks at each cost;
at cost 0.80 its illustrative utility was 0.600, **better** than the
new rule's 0.567. Therefore the rule is not uniformly superior and does not
establish calibrated decision quality. Its defensible positive effect is
that **increasing a declared cost now changes the proposal without falsifying
the original model evidence**. It is deliberately optional.

Private, reproducible **off-Git** cost-replay script:
`D:\VERA\_agent-work\bt2-vera-adaptive-choice-20261121-private-receipts\v4_cost_assumption_replay_v1.py`
SHA-256 `76f9ab2b0d6904d143020cd611c020295d5e9e5c7057d31fe744ab195653642e`.

Private results receipt:
`D:\VERA\_agent-work\bt2-vera-adaptive-choice-20261121-private-receipts\v4-cost-assumption-replay-20261121-private.json`
SHA-256 `edccafbed1a03ea17a087f7ddbbad90a1e82348c9b3672c8af892a0527d364b5`.

The private experiment had only public arithmetic, no user data. No
protected runtime activation, canonical memory write, model-weight change,
production tool connection, merged code, or authorizing review was performed.
