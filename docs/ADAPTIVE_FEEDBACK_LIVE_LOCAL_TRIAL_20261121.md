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


## 2026-11-21 source audit: reject unsupported feature extrapolation

The optional `choose_with_cost_assumption` method added in the preceding
research commit initially checked that all historical feedback came from
one recorded cost. That alone did **not** mean the learned ANSWER score
was supported at the new request's uncertainty/consequence pair. It
accepted an arbitrary unseen pair and even a pair for which only VERIFY
feedback had ever been admitted, while comparing that pair's **unobserved**
ANSWER score with a claimed verification benefit.

The source now **fails closed** unless its ordered feedback history
contains at least one `ANSWER` observation at the exact requested
`(uncertainty, consequence)` pair, with the already required common
`reference_cost`. Thus a new pair inside the old min/max range is still
rejected, as is a target supported only by VERIFY observations.
A subsequent restored snapshot enforces the same condition because the
guard reads the restored ordered history. The decision and state schema
are otherwise unchanged.

Three new tests were observed RED before repair and GREEN afterward:
unseen pairs rejected, same check survives snapshot restore, and
VERIFY-only or unrelated ANSWER feedback cannot stand in for ANSWER
evidence at the requested pair. Valid, supported decisions remain
read-only and leave the learned state unchanged.

A fresh **source replay**, not new Ollama inference or training,
reopened the previous frozen V4 arithmetic receipt
`6926bd062a9d0a717b1306b36d609f1a5a9fdead21f6a1d412c38ac43020fdad`
and confirmed that all 30 saved questions still obtain the same
previously reported proposals at assumed costs:
0.02 -> 30 VERIFY; 0.24 -> 20; 0.80 -> 0; 1.00 -> 0.
Two new unsupported pairs `(.3,.7)` and `(.9,.9)` correctly failed
closed. Full local source suite **320/320 PASS**; expected
pytest-asyncio deprecation warning remains.

**Important unsolved limitation:** numerical feature support is not
task-family binding, provenance authentication, calibration, statistical
confidence or proof of independent action outcome. Character-counting
questions can reuse the exact same numeric uncertainty/consequence bins
as arithmetic and therefore still pass this guard while performing
badly. This repair prevents one form of evidence extrapolation; it does
**not** qualify general transfer. The other reviewer already observed
11/24 correctness on a nonarithmetic family and medium group 0/8,
so the next release gate still requires an independently specified
task-family contract, heldout qualification and trusted verifier
outcomes. No effect authority was added, no runtime deployed, and the
PR remains a source-only draft.


## 2026-11-21 follow-up: optional family-scoped source-bound feedback

An independent reviewer already demonstrated that the frozen arithmetic learner
did not transfer reliably to letter-counting (11/24 final correct, medium
0/8). The preceding fix restricted the numerical (uncertainty,
consequence) pair, but **the exact same numbers can describe a different
task family**. There was no genuine family evidence in the historical
`AdaptiveChoiceProbe` snapshot, so copying it into another domain would
silently manufacture the missing binding.

This small source candidate introduces an **opt-in separate**
`ScopedAdaptiveChoiceProbe`. It uses a distinct underlying
`AdaptiveChoiceProbe` instance for each explicitly named task family,
bound to exactly one lower-case SHA-256 source digest. Unknown families
are **rejected without fallback** rather than inheriting weights based
on matching numerical features. A source digest change for an existing
family also rejects; replayed event IDs reject across all families.
A failed new-family observation cannot create a family. Strict snapshots
retain the family, digest, and ordered existing replayable feedback;
restoring them enforces family isolation, duplicated family/receipt
checks, and original source-derived numerical weights.

This is **not automatic task classification**. Family identifiers and
source hashes are *caller-asserted*, and the hash is merely a content
equality binding, not trusted proof that feedback truly came from a
particular task family, that outcomes are authentic, or that the source
is independently verified. A caller that lies consistently about the
family can still contaminate it. No active VolitionEngine uses this
wrapper; it is source-only and does not migrate legacy unscoped history.
The original `AdaptiveChoiceProbe` API and historical snapshot schema
are unchanged.

The first four domain-separation tests were RED before implementation;
a fifth rejected alias-like noncanonical family tags (e.g. repeated
periods) after a separate RED→GREEN correction. Test cases cover a
string-count request with exactly the same numeric evidence as
arithmetic, independent family updates, cross-family replay prevention,
source-digest mismatches, tampered restored snapshots, invalid tags,
and no silent fallback.

### Read-only reconstruction from actual prior local-model feedback

Without asking the local model another question or retraining it on
new data, I reopened the SHA-pinned V4 arithmetic trial receipt
`6926bd062a9d0a717b1306b36d609f1a5a9fdead21f6a1d412c38ac43020fdad`.
I re-fed its 36 historically observed arithmetic training cases as
72 ordered action-feedback updates into one scoped family
`arithmetic.integer`, using the *exact V4 receipt digest* as the
source identity, and replayed the original 40 extra numerical
consolidation epochs.

**The resulting scoped underlying probe snapshot matched the stored
original V4 learner snapshot exactly**, including all weights,
recorded events and epoch count. A fresh scoped restore preserved that
identity. Its 30 frozen arithmetic evaluation proposals were unchanged
at test costs 0.02→30 VERIFY, 0.24→20, 0.80→0 and 1.00→0. The
`strings.letter_count` family with identical numerical features
rejected `unbound task family`; using a different source digest with
the arithmetic label rejected `source digest mismatch`.

This verifies a **source/feedback-state reconstruction and explicit
cross-family rejection**. It does **not** repeat the independent
letter-counting model test, qualify production routing, attest model
binary identity, authorize effects, or demonstrate subjective
autonomy, awareness, or generalized learning. A genuine deployment
would require externally established task-family classification,
trusted source and outcome attestation, a controlled family-specific
heldout suite, an actual verifier provider and owner-approved runtime
binding. Until then, no merge/install is asserted.


## 2026-11-21 explicit-growth challenge: trained *separate* string-count family

**Motivating falsifier:** Independent reviewer of earlier arithmetic-trained
candidate found weak transfer to 24 fresh character-count items
(11/24 correct after verification, medium group 0/8). A family boundary
prevents contamination but, by itself, creates **no new competence**.
I therefore ran one **new, pre-seeded**, separately trained string-count
trial using the existing, already-running local
`vera-successor:0.8b-context` Ollama model. No old private dialogs or
personal content were used: all questions are newly generated synthetic
lowercase character strings.

### New optional trial source and result

`scripts/local_letter_feedback_trial.py` defines a closed public protocol
`strings.letter_count` with target characters `a/e/i/t` and
difficulty levels of lengths 6, 13 and 27. Fixed generation seeds
`31031` (36 training questions, twelve per level) and `88500`
(30 heldout, ten per level) were frozen before execution. All 66
questions are unique with **zero cross-split overlap**.
Protocol digest is a caller-supplied equality marker, not source attestation.

Each actual model response was compared to a deterministic Python
`word.count(target)` reference. For each of 36 training observations,
the probe received two action-preference *labels* (ANSWER if model
correct, otherwise VERIFY); these are **toy preference labels**, not
separately witnessed VERIFY outcomes. The only trainable parameters
are 10 logistic decision-head weights inside the opt-in
`ScopedAdaptiveChoiceProbe`; the underlying Ollama model was
**not trained or changed**. After 40 previously selected consolidation
epochs, the separate family snapshot was frozen and independently
restored before the heldout was evaluated.
For each heldout decision the actual local model returned its own
short integer, and the selected VERIFY route invoked a *real*
deterministic in-process character-count implementation. Bad or
missing verifiers cannot silently pass.

**Actual observed result:** local model correct **1/30 (3.3%)**;
trained scoped rule selected VERIFY on **30/30**; executed
character-count results correct **30/30 (100%)**, one unnecessary
verification. The underlying local model's extremely poor results
may reflect task wording, model decoding or its task ability:
this small one-prompt trial does not diagnose why it failed, or
prove general model incompetence.

**Crucial negative control:** assuming a 0.24 per-check utility
penalty and a perfect deterministic verifier, both the learned
head and a trivial **ALWAYS VERIFY** baseline score
`1 - 0.24 = 0.76`. The learned policy showed **zero excess
utility over the best fixed policy**, and did not learn
selective verification. Its apparent 96.7 percentage-point
accuracy increase is simply the calculator replacing the
model's unreliable answers. The previously observed narrow
arithmetic trial did have some selective gain over this trivial
comparison; this **different** domain did not.

This is the counterexample I wanted. Improving a result by
handing all work to a deterministic oracle does not justify
claiming a better general decision-maker, meaningful new
Vera preferences, or a change in ChatGPT weights. It **does**
demonstrate strict source-family separation, repeatable numerical
feedback-state updates, actual verifier routing, and a concrete
failure case that a qualification process must reject.

### Exact custody and reproducibility

The raw trial JSON and sidecar were written *outside tracked Git*
to private Lappy:
`D:\VERA\_agent-work\bt2-vera-adaptive-choice-20261121-private-receipts\letter-count-scoped-trained-20261121-v1.json`.

Exact SHA-256 of immutable V1 receipt:
`bbe901061ef6e7e2c1b949d798d7e6c8b1f4a35527e9e1bcca83390359425390`.

A fresh separate Python process reopened this exact receipt,
verified its sidecar and digest, reconstructed the learned
`strings.letter_count` scope from 72 recorded action-preference
feedback events plus 40 consolidation passes, reproduced all
30 heldout choices, independently recomputed every public
character count, and checked that model correctness,
verification flags, and final correctness agreed with the
record. Exact generator seeds and train/holdout uniqueness were
checked again. No redrive of the 66 model queries was needed.

After the immutable V1 run I added
`evaluate_fixed_policy_controls` to future script outputs,
explicitly comparing policy utility against both always-ANSWER
and an *assumed-perfect* always-VERIFY rule. It labels
an all-VERIFY or all-ANSWER run as `TRIVIAL`, never
`SELECTIVE_GAIN_CANDIDATE`. Three adversarial tests were RED
for the missing comparator, then GREEN; the original V1
receipt was **not** retroactively changed. The comparison
was independently calculated against its saved counts.

### Limits / required next evidence

- This was not a hidden external evaluator: model prompt,
  protocol digest, generator, oracle and reward assumptions
  were authored within the same test harness.
- Family/source labels and outcome labels remain caller asserted,
  untrusted. A malicious caller can choose consistent lies.
- The binary preferred-action labels are not directly
  measured cost-sensitive reward for the VERIFY alternative.
- The verifier and the reference are both local deterministic
  Python; not an independently authenticated provider.
- Task difficulty, source prompt sensitivity, parameter drift,
  cost diversity, model provenance and transfer to other tasks
  remain unqualified.
- A genuine *selective* learner qualification needs a
  separately heldout task family/distribution with both
  trustworthy model-correct and verifier-success outcomes,
  measured route cost and a fixed baseline that beats
  both naive rules. Do **not** promote, merge or install
  the source on this result.

This private research artifact advances testability and
correctness of claims, not proof of first-person experience,
long-term identity, user consent, or active production capability.


### Hosted CI portability correction for this source head

The first GitHub run for commit `3acfd1d37af755b085bc7c4cfefca4d4b711ff4a`
**FAILED** Python 3.11/3.12/3.13 and workspace-startup tests despite
333/333 passing on Windows Lappy. Exact failed log showed one problem:
`test_letter_family_valid_private_receipt_target_is_accepted_without_creation`
mistook the literal Windows drive-qualified receipt fixture for an
absolute path on Linux. It was a **test portability bug**, not a local
model inference failure. Hosted CodeQL still passed.

The next source-only correction changes that single test to use
pytest's cross-platform `tmp_path` plus `monkeypatch` for the
trial's receipt-directory constant, exercising the same receipt
containment rule on Windows and Linux. The actual Lappy trial
continues to use the fixed private Windows receipt directory.
No raw receipt, learned policy weight, original sample,
production route or model was changed. Hosted CI must be checked
against the new exact commit, never inferred from local tests.


## 2026-11-21 second owner challenge: 90 fresh frozen-policy questions

**Preregistered decision:** Freeze the V4 `AdaptiveChoiceProbe` weights
without new feedback, tuning, or changes to its `choose()` rule; test it
on three batches of 30 genuinely new structured arithmetic questions.
Each batch must show strictly greater illustrative utility than
**both** always-ANSWER and assumed-perfect always-VERIFY at the
predeclared cost `0.24`. All three batches, not merely their pooled
aggregate, must pass. This is a research replication test, **not**
a production model qualification or actual measured verification cost.

### Split construction and prospective correction

The original "easy" addition generator allowed only 8×8 = 64 ordered
questions. Excluding the four older studies exhausted its unused
easy-question space, so the first attempted preregistration aborted
before saving any preregistered question set or calling the model.
I corrected the **question generator before observing any new model
answer** to widen "easy" addition operands from 2..9 to **2..19**.
The old numerical context uncertainty of 0.15 remains unchanged. This
is intentionally a **distribution-shift** challenge, and is not
the same distribution as the original V4. Medium and hard ranges are
unchanged.

The corrected frozen generator produced 90 unique questions, using
seeds `61741`, `23147`, `86720`, with no overlap against earlier
arithmetic v1–v4 training/holdout receipts, or between new batches.
The exact complete list of all 90 questions, exclusion source names and
SHA-256s, protocol assumptions, and strict pass criteria were written
as an immutable private preregistration **before** any new Ollama
inference.

Preregistration JSON SHA-256:
`ba35bc301bcbb3c751fe7107cef42443694336abfac74bd5fb71d5c5307ebac3`.

### Actual observed model and policy outcomes

The existing local `vera-successor:0.8b-context` answered all 90
new questions via its already-running Ollama loopback endpoint. The
source policy was restored from the immutable **V4** local model
receipt SHA-256
`6926bd062a9d0a717b1306b36d609f1a5a9fdead21f6a1d412c38ac43020fdad`.
Every VERIFY choice executed the local Python integer oracle; no model
or decision-head weights were changed.

| Seed | Model only correct | Model + selected checks correct | Executed checks | Policy utility | Best fixed utility | Excess |
|---|---:|---:|---:|---:|---:|---:|
| 61741 | 19/30 | 25/30 | 10 | 0.7533 | 0.7600 | **−0.0067** |
| 23147 | 20/30 | 27/30 | 10 | 0.8200 | 0.7600 | +0.0600 |
| 86720 | 19/30 | 26/30 | 10 | 0.7867 | 0.7600 | +0.0267 |
| **Pooled** | **58/90** | **78/90** | **30** | **0.7867** | **0.7600** | **+0.0267** |

**Predeclared replication qualification: FAILS** because the first
batch lost to the fixed control. The pooled score does not override
the three-batch pass criterion, and two favorable batches are
insufficient to establish stable transfer. These results were not
used to change epochs, costs, features or policy weights.

### The stronger falsifier: the fixed oracle dominates this environment

All 90 model inferences together took about **19.6433 seconds**
on the existing Lappy loopback service. The actual 30 selected
in-process calculator calls together took **0.0000714 seconds**.
During separate fresh-process readback, evaluating all 90 simple
already-parsed arithmetic tasks directly using Python `operator.add`
and `operator.mul` produced **90/90 correct in 0.0001755 seconds**
of in-process computation. These are local process measurements;
a full external tool invocation, parsing natural-language questions,
trust checks and host service latency were **not measured**.

The assumed 0.24 verification cost is therefore not empirically
justified for this cheap local deterministic oracle. If the task is
already a structured pair of integers and an operator, **always
calculate** dominates calling an LLM first on both accuracy and
observed local computation time. The original task family is a
poor proving ground for economically meaningful learned selectivity.

**Strongest defensible inference:** The frozen local policy can route
some model errors to a tool, but does not pass strict replication
and does not establish a useful, cost-optimal, general decision-maker.
The prior string-count experiment likewise proved no advantage
over always verify. Continuing to tune the arithmetic selector
against an arbitrary check-cost scale would risk benchmarking
the benchmark, not developing genuine judgment.

### Custody, verification, and next real frontier

The actual private source script, preregistration, and raw outcome
receipt are retained **outside Git** in Lappy's authorized
`D:\VERA\_agent-work\bt2-vera-adaptive-choice-20261121-private-receipts`
directory. Exact outcome JSON SHA-256:
`7b065e7d46500fe58461cd0145747168327c2157e63f225c2e06195771dbb6af`.

A fresh independent Python interpreter (same host, separate process)
checked both receipt and preregistration SHA sidecars, all 90
preregistered question strings, no overlap against earlier trials,
all actions reproduced from frozen V4 weights, original model
and final-answer correctness recomputed from operands, verifier
execution flags, per-batch utility, and unchanged model-choice
weights. **All checks passed.** This was not an independently
custodied external evaluator, and the harness was authored by
the source owner.

No merge, model training, production runtime installation, identity
change, permission/canonical memory mutation, or trusted cost provider
is implied. The next substantive qualification needs an actual
cost-bearing **nontrivial verifier**, with authenticated outcomes,
externally held-out tasks, and a fixed rule that beats both
always-verify and never-verify without tuning on the test set.
Until then the research PR should remain **OPEN DRAFT**.
