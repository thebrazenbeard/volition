# Volition Core V1 Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a deterministic, provenance-aware Volition V1 that turns typed motive evidence into wants, choices, persistent goals, bounded cognition requests, and durable SQLite state without granting external effect authority.

**Architecture:** Extend the existing deterministic engine at `f69f4a7` rather than rewriting it. Preserve the current drive-scoring behavior, add explicit lifecycle records and replay/currentness rules, then put durable records behind a small SQLite store. Project Runner remains the execution supervisor; external effects stay outside the package.

**Tech Stack:** Python 3.11+, dataclasses, enums, sqlite3, hashlib/json from the standard library, pytest.

## Global Constraints

- `SIGNAL != SALIENCE != DRIVE != WANT != CHOICE != GOAL != CONSENT != AUTHORITY != ACTION != OUTCOME != PHENOMENOLOGY`.
- Drives remain typed; no global master reward scalar.
- Historical evidence cannot silently reactivate a current want.
- Protection/refusal/revocation can veto ordinary approach.
- Social approval is capped and cannot manufacture self-authored choice.
- Endogenous cognition is bounded and never carries effect authority.
- Every durable transition is reconstructible and receipt-bearing.
- Private donor content is not copied into this public repository.
- No merge, deployment, provider mutation, or native Project install is implied by source completion.

---

### Task 1: Repository hygiene and persistence baseline

**Files:**
- Create: `.gitignore`
- Modify: `pyproject.toml`
- Modify: `src/volition/engine.py`
- Modify: `src/volition/models.py`
- Test: `tests/test_persistence.py`

**Interfaces:**
- Consumes: `VolitionEngine.snapshot()`, `VolitionEngine.from_snapshot()`, `VolitionEngine.events`
- Produces: clean source tree, stable snapshot schema, warning-free pytest configuration where project-controlled.

- [ ] Remove committed `__pycache__`/bytecode from Git and ignore `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, and local SQLite files.
- [ ] Preserve the already-verified snapshot/restore behavior and authority boundary; classify it as tests-after evidence because red was not observed before implementation.
- [ ] Add malformed snapshot cases for non-contiguous events, negative elapsed time, over-budget cognition count, and authority-bearing restored objects.
- [ ] Run `python -m pytest -q tests/test_persistence.py`; expected: all persistence tests pass.
- [ ] Run `python -m pytest -q tests/test_engine.py tests/test_persistence.py`; expected: all current engine and persistence tests pass.
- [ ] Commit the independently passing hygiene/persistence baseline.

### Task 2: Explicit want, choice, and goal lifecycle

**Files:**
- Modify: `src/volition/models.py`
- Modify: `src/volition/engine.py`
- Test: `tests/test_lifecycle.py`
- Modify: `src/volition/__init__.py`

**Interfaces:**
- Produces: `WantRecord`, `ChoiceRecord`, `ChoiceClass`, `GoalStatus`, `VolitionEngine.choose(...)`, `VolitionEngine.adopt_choice(...)`
- Compatibility: current `evaluate()`, `tick()`, and `adopt()` remain available, but any goal creation routes through an explicit recorded choice internally.

- [ ] Red: add a test proving a want does not itself create a goal and a goal cannot be adopted from an unknown/invalid choice.
- [ ] Run the focused lifecycle test; expected: non-zero assertion/attribute failure caused by missing choice lifecycle.
- [ ] Green: add deterministic want/choice IDs, typed choice provenance (`SELF_AUTHORED`, `USER_DIRECTED`, `POLICY_DERIVED`, `MODEL_PROPOSED`), goal statuses, and transition receipts.
- [ ] Add lifecycle tests for revise/revoke/complete/stale transitions; revoked state cannot silently revive.
- [ ] Add a test proving model-proposed and self-authored choices remain distinguishable.
- [ ] Run focused lifecycle tests, then the full suite.
- [ ] Commit the passing lifecycle deliverable.


### Task 3: Durable SQLite store, replay safety, and currentness

**Files:**
- Create: `src/volition/store.py`
- Modify: `src/volition/engine.py`
- Modify: `src/volition/__init__.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Produces: `VolitionStore(path)`, `store.ingest_signal(...)`, `store.persist_engine(...)`, `store.load_engine(...)`, `store.receipts(...)`
- Durable tables: `signals`, `drive_states`, `wants`, `choices`, `goals`, `receipts`, `cognition_requests`.

- [ ] Red: add a test that creates a SQLite store, persists a selected goal and receipts, closes/reopens, and reconstructs the same goal/current lifecycle.
- [ ] Red: add duplicate-signal tests: exact replay is idempotent; same signal ID with divergent canonical payload raises `ValueError`.
- [ ] Implement schema creation with WAL and foreign keys enabled, canonical JSON payloads, SHA-256 request digests, transactions, and append-only receipts.
- [ ] Implement optimistic revision checks for mutable projections so stale writes fail instead of overwriting current state.
- [ ] Add tests for stale revision failure and receipt ordering across reopen.
- [ ] Run focused store tests; expected: pass.
- [ ] Run the full suite; expected: pass.
- [ ] Commit the passing durability/replay deliverable.

### Task 4: Hostile arbitration, currentness, and anti-self-stimulation

**Files:**
- Modify: `src/volition/engine.py`
- Modify: `src/volition/models.py`
- Test: `tests/test_hostile.py`

**Interfaces:**
- Consumes: typed drive contributions and lifecycle records.
- Produces: explicit `CONFLICTED`, `STALE`, veto/suppression reasons, and bounded `CognitionRequest` records.

- [ ] Red: test that conflicting approach/protection evidence remains visible and is not erased by scalar cancellation.
- [ ] Red: test that stale historical desire stays stale until a fresh current reappraisal event.
- [ ] Red: test that social approval cannot revive an explicitly revoked want.
- [ ] Red: test that novelty/epistemic stimulation without information gain or learning progress cannot self-renew indefinitely.
- [ ] Implement the minimum policy changes needed for those behaviors while preserving each motive-family contribution in receipts.
- [ ] Add cognition-request tests proving no capability/effect-authority field can be minted by Volition and endogenous request count remains bounded across snapshot/store recovery.
- [ ] Run focused hostile tests, then the full suite.
- [ ] Commit the passing hostile-policy deliverable.

### Task 5: Inspection surface, documentation, and qualification

**Files:**
- Create: `src/volition/cli.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/RESEARCH_LEDGER.md`
- Create: `docs/reviews/2026-10-06-volition-v1-hostile-review.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces CLI commands for read-only `status`, `goals`, and `receipts` against a SQLite store.
- No CLI command dispatches external tools or mutates external systems.

- [ ] Red: add CLI tests for an empty store and a populated store; output must show lifecycle facts without claiming consciousness, felt desire, or authority.
- [ ] Implement the minimum CLI and register the console script in `pyproject.toml`.
- [ ] Update README with architecture, quick start, claim ceiling, source provenance, and explicit integration seam to Pre-Active.
- [ ] Append research-ledger entries for internal synthesis, external prior art, design freeze, implementation heads, and test evidence.
- [ ] Run an internal hostile review against the exact candidate head, explicitly challenging reward collapse, approval capture, stale-want resurrection, authority inflation, replay, interruption persistence, and phenomenology laundering.
- [ ] Run `python -m pytest -q`; expected: complete suite passes.
- [ ] Run `python -m compileall -q src tests`; expected: exit 0.
- [ ] Verify `git status --short` is clean and remote branch head equals local head after push.
- [ ] Open a pull request to `main` if the branch is complete. Do not merge: merge remains Patrick-controlled protected authority.

## Externally observable decisions

The product contract fixes the important externally visible choices for V1: deterministic Python engine, SQLite persistence, explicit choice provenance, no external effect API, and read-only inspection CLI. No additional product decision is currently blocking implementation. Compatibility wrappers may preserve already-tested pre-release methods only when they still route through the stricter lifecycle invariants; they may not bypass them.

