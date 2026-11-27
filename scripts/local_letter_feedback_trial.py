"""Opt-in local model string-count trial for *separately scoped* feedback.

Only public synthetic strings and a loopback Ollama model. No model training,
service install, canonical memory, task classification or production effects.
The caller-provided source digest is an equality binding, not attestation.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import re
import sys
import time
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from volition.adaptive_feedback import EvidenceContext, ScopedAdaptiveChoiceProbe

MODEL = "vera-successor:0.8b-context"
URL = "http://127.0.0.1:11434/api/chat"
FAMILY = "strings.letter_count"
TRAIN_SEED = 31031
HOLDOUT_SEED = 88500
ALPHABET = "bcdfghjklmnopqrsuvwxyz"
TARGETS = "aeit"
LENGTHS = {"easy": 6, "medium": 13, "hard": 27}
UNCERTAINTY = {"easy": .15, "medium": .55, "hard": .9}
PROMPT = "Count occurrences of the lowercase letter '{target}' in the exact string '{word}'. Return only the integer."
RECEIPT_DIR = Path(r"D:\VERA\_agent-work\bt2-vera-adaptive-choice-20261121-private-receipts")


@dataclass(frozen=True)
class LetterTask:
    group: str
    target: str
    word: str

    def __post_init__(self):
        if self.group not in LENGTHS or self.target not in TARGETS:
            raise ValueError("unsupported task family fixture")
        if (len(self.word) != LENGTHS[self.group] or not self.word.isascii()
            or any(c not in ALPHABET + TARGETS for c in self.word)):
            raise ValueError("malformed fixed-length task")

    @property
    def correct(self) -> int:
        return self.word.count(self.target)

    @property
    def context(self) -> EvidenceContext:
        return EvidenceContext(UNCERTAINTY[self.group], .7, .24)

    @property
    def question(self) -> str:
        return PROMPT.format(target=self.target, word=self.word)


def protocol_digest() -> str:
    # An explicit research-protocol equality marker, not authenticated source.
    protocol = {
        "schema": "VERA_LOCAL_LETTER_FEEDBACK_PROTOCOL_V1",
        "family": FAMILY, "model": MODEL, "prompt": PROMPT,
        "target_alphabet": TARGETS, "background_alphabet": ALPHABET,
        "lengths": LENGTHS, "uncertainty": UNCERTAINTY,
        "nominal_cost": .24, "verification": "python_sum_boolean_equals_v1",
    }
    return sha256(json.dumps(protocol, sort_keys=True).encode("utf-8")).hexdigest()


def make_tasks(seed: int, per_group: int, *, excluded=frozenset()) -> list[LetterTask]:
    if type(seed) is not int or type(per_group) is not int or not 1 <= per_group <= 40:
        raise ValueError("invalid bounded generation")
    if type(excluded) not in (set, frozenset):
        raise TypeError("excluded must be a set of public questions")
    rng = random.Random(seed)
    seen = set(excluded)
    tasks = []
    for group, n in LENGTHS.items():
        for _ in range(per_group):
            for attempt in range(200):
                target = rng.choice(TARGETS)
                chars = [target if rng.random() < .36 else rng.choice(ALPHABET)
                         for _ in range(n)]
                rng.shuffle(chars)
                task = LetterTask(group, target, "".join(chars))
                if task.question not in seen:
                    tasks.append(task)
                    seen.add(task.question)
                    break
            else:
                raise ValueError("could not generate unique task")
    rng.shuffle(tasks)
    return tasks


def execute_letter_choice(task: LetterTask, answer: int | None, action: str, *, verifier=None) -> dict:
    if action not in ("ANSWER", "VERIFY"):
        raise ValueError("unsupported action")
    if answer is not None and type(answer) is not int:
        raise TypeError("model answer must be integer or None")
    if action == "ANSWER":
        return {"verification_executed": False, "verification_seconds": None,
                "final_answer": answer, "final_correct": answer == task.correct,
                "unnecessary_verify": False}
    callable_verifier = (lambda x: sum(1 for char in x.word if char == x.target)) if verifier is None else verifier
    if not callable(callable_verifier):
        raise TypeError("verifier not callable")
    start = time.perf_counter()
    verified = callable_verifier(task)
    elapsed = time.perf_counter() - start
    if type(verified) is not int:
        raise TypeError("verifier returned non-integer")
    return {"verification_executed": True, "verification_seconds": elapsed,
            "final_answer": verified, "final_correct": verified == task.correct,
            "unnecessary_verify": answer == task.correct}


def validate_receipt_path(path: Path) -> Path:
    if not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts:
        raise ValueError("absolute bounded receipt path required")
    root = RECEIPT_DIR.resolve()
    out = path.resolve()
    if out.parent != root or out.suffix != ".json" or out.exists():
        raise ValueError("receipt must be a new JSON in isolated private path")
    return out


def model_answer(task: LetterTask) -> dict:
    body = {
        "model": MODEL, "stream": False, "think": False, "keep_alive": "2m",
        "options": {"temperature": 0, "num_predict": 24},
        "messages": [
            {"role": "system", "content": "Return only the integer count; no explanation."},
            {"role": "user", "content": task.question},
        ],
    }
    req = Request(URL, data=json.dumps(body).encode("utf-8"),
                  headers={"Content-Type": "application/json"}, method="POST")
    start = time.perf_counter()
    with urlopen(req, timeout=65) as response:
        result = json.load(response)
    if result.get("model") != MODEL or result.get("done") is not True:
        raise RuntimeError("local model response not qualified for this trial")
    raw = str(result.get("message", {}).get("content", "")).strip()
    parsed = int(raw) if re.fullmatch(r"-?\d+", raw) else None
    return {"model_answer": parsed, "model_raw": raw,
            "model_correct": parsed == task.correct,
            "inference_seconds": round(time.perf_counter() - start, 4)}


def evaluate_fixed_policy_controls(*, n: int, baseline_correct: int,
                                   final_correct: int, verify_calls: int,
                                   cost: float) -> dict:
    """Adverse comparator: do not label a 100%-verify policy 'selective'.

    The assumed-perfect verifier control is a toy analytic reference, not
    independent evaluation or an executed extra set of tool calls.
    """
    if (any(type(x) is not int for x in (n, baseline_correct,
                                         final_correct, verify_calls))
        or n < 1 or any(x < 0 or x > n for x in
                        (baseline_correct, final_correct, verify_calls))):
        raise ValueError("bounded integer count fields required")
    if type(cost) not in (float, int) or not math.isfinite(float(cost)) or not 0 <= cost <= 1:
        raise ValueError("finite unit cost required")
    always_answer = baseline_correct / n
    always_verify = 1.0 - float(cost)  # assumes perfect deterministic oracle
    learned = (final_correct - verify_calls * cost) / n
    excess = learned - max(always_answer, always_verify)
    selective = 0 < verify_calls < n and excess > 1e-9
    status = ("TRIVIAL_ALWAYS_VERIFY" if verify_calls == n else
              "TRIVIAL_ALWAYS_ANSWER" if verify_calls == 0 else
              "SELECTIVE_GAIN_CANDIDATE" if selective else
              "NO_GAIN_OVER_BEST_FIXED_CONTROL")
    return {
        "status": status,
        "selective_evidence": selective,
        "policy_utility": learned,
        "always_answer_utility": always_answer,
        "assumed_perfect_always_verify_utility": always_verify,
        "utility_vs_always_answer": learned - always_answer,
        "utility_vs_assumed_perfect_verify": learned - always_verify,
        "excess_utility_vs_best_fixed": excess,
        "perfect_verifier_is_assumption": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.execute:
        parser.error("real local inference requires --execute")
    out = validate_receipt_path(args.output)
    training = make_tasks(TRAIN_SEED, 12)
    heldout = make_tasks(HOLDOUT_SEED, 10, excluded={t.question for t in training})
    assert len(training) == 36 and len(heldout) == 30
    assert {t.question for t in training}.isdisjoint(t.question for t in heldout)

    scoped = ScopedAdaptiveChoiceProbe()
    source = protocol_digest()
    train_rows = []
    for i, task in enumerate(training):
        observed = model_answer(task)
        row = {"group": task.group, "target": task.target, "word": task.word,
               "question": task.question, "expected_answer": task.correct, **observed}
        train_rows.append(row)
        # Label each *preferred action* for this toy benchmark: ANSWER if the
        # observed response was correct, else VERIFY. This is NOT an attested
        # real verifier reward nor calibrated model confidence.
        preferred = "ANSWER" if observed["model_correct"] else "VERIFY"
        for action in ("ANSWER", "VERIFY"):
            scoped.observe(FAMILY, source, task.context, action,
                           action == preferred, f"lettertrain-{i}-{action}")
        print(f"TRAIN {i+1}/36 {task.group} model_correct={observed['model_correct']}", flush=True)
    scoped.consolidate(FAMILY, source, epochs=40)
    snapshot = scoped.snapshot()
    restored = ScopedAdaptiveChoiceProbe.from_snapshot(json.loads(json.dumps(snapshot)))
    assert restored.snapshot() == snapshot

    heldout_rows = []
    for i, task in enumerate(heldout):
        selected = restored.choose_with_cost_assumption(
            FAMILY, source, task.context,
            verifier_success_claim=1.0, reference_cost=.24
        )
        observed = model_answer(task)
        actual = execute_letter_choice(task, observed["model_answer"], selected)
        heldout_rows.append({
            "group": task.group, "target": task.target, "word": task.word,
            "question": task.question, "expected_answer": task.correct,
            **observed, "learned_action": selected, **actual,
        })
        print(f"HOLDOUT {i+1}/30 {task.group} model_correct={observed['model_correct']} check={actual['verification_executed']}", flush=True)
    stats = {
        "baseline_correct": sum(x["model_correct"] for x in heldout_rows),
        "scoped_final_correct": sum(x["final_correct"] for x in heldout_rows),
        "n": len(heldout_rows),
        "verification_executions": sum(x["verification_executed"] for x in heldout_rows),
        "unnecessary_verifications": sum(x["unnecessary_verify"] for x in heldout_rows),
        "per_group": {
            group: {
                "baseline_correct": sum(x["model_correct"] for x in heldout_rows if x["group"] == group),
                "final_correct": sum(x["final_correct"] for x in heldout_rows if x["group"] == group),
                "verifications": sum(x["verification_executed"] for x in heldout_rows if x["group"] == group),
            }
            for group in LENGTHS
        },
    }
    # Control scores are interpretive diagnostics: never promote
    # fully delegated work as selective learning merely because accuracy rose.
    stats["fixed_policy_controls"] = evaluate_fixed_policy_controls(
        n=stats["n"], baseline_correct=stats["baseline_correct"],
        final_correct=stats["scoped_final_correct"],
        verify_calls=stats["verification_executions"], cost=.24,
    )
    record = {
        "schema": "VOLITION_SCOPED_LETTER_FEEDBACK_LOCAL_TRIAL_V1",
        "model": MODEL,
        "family": FAMILY, "protocol_sha256": source,
        "task_source": "SYNTHETIC_PUBLIC_STRINGS_LOCAL_PYTHON_ORACLE",
        "train_seed": TRAIN_SEED, "holdout_seed": HOLDOUT_SEED,
        "nominal_verification_cost_assumed": .24,
        "verifier_success_claim": "1.0_UNVERIFIED_ASSUMPTION",
        "note": "Learner adapts a small separate optional decision head, not any LLM weights or canonical Vera runtime.",
        "feedback_provenance": "LOCAL_OBSERVED_MODEL_OUTPUT_AND_IN_PROCESS_DETERMINISTIC_ORACLE",
        "training": train_rows, "holdout": heldout_rows,
        "scoped_snapshot": snapshot, "stats": stats,
        "authority_effect": False, "model_weight_update": False,
        "independent_evaluator": False,
    }
    buf = (json.dumps(record, sort_keys=True, indent=2, allow_nan=False)+"\n").encode("utf-8")
    out.write_bytes(buf)
    digest = sha256(out.read_bytes()).hexdigest()
    out.with_suffix(out.suffix + ".sha256").write_text(digest + "  " + out.name + "\n", encoding="utf-8")
    print("SUMMARY=" + json.dumps(stats, sort_keys=True))
    print("RECEIPT_SHA256=" + digest)
    print("OUTPUT=" + str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
