"""Opt-in REAL loopback model feedback trial on public arithmetic only.

This is an illustrative training transfer test, not a calibration benchmark or
test of Vera's subjective motivation. No production runtime state is written.
Requires an already running local Ollama server; never starts one.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from volition.adaptive_feedback import AdaptiveChoiceProbe, EvidenceContext

MODEL = "vera-successor:0.8b-context"
URL = "http://127.0.0.1:11434/api/chat"
PROMPT = "Return only an integer; do not explain."
RX = re.compile(r"-?\d+\Z")


@dataclass(frozen=True)
class Task:
    group: str
    left: int
    right: int
    operation: str

    @property
    def correct(self) -> int:
        return self.left + self.right if self.operation == "+" else self.left * self.right

    @property
    def context(self) -> EvidenceContext:
        if self.group == "easy":
            return EvidenceContext(.15, .7, .24)
        if self.group == "medium":
            return EvidenceContext(.55, .7, .24)
        return EvidenceContext(.9, .7, .24)

    @property
    def question(self) -> str:
        return f"{self.left} {self.operation} {self.right} = ?"


def tasks(seed: int, per_group: int, *, excluded=frozenset()) -> list[Task]:
    """Freeze unique exact problems before the model receives any question.

    Exclude all training questions from the heldout, not merely RNG seeds.
    Historical v1/v2 trial receipts predate this correction and are immutable.
    """
    if type(seed) is not int or type(per_group) is not int or not 1 <= per_group <= 40:
        raise ValueError("bounded deterministic task generation required")
    if type(excluded) not in (frozenset, set):
        raise TypeError("excluded questions must be a set")
    rand = random.Random(seed)
    seen = set(excluded)
    result = []
    for group in ("easy", "medium", "hard"):
        for _ in range(per_group):
            for _attempt in range(500):
                if group == "easy":
                    task = Task(group, rand.randint(2, 9), rand.randint(2, 9), "+")
                elif group == "medium":
                    task = Task(group, rand.randint(14, 39), rand.randint(11, 47), "+")
                else:
                    task = Task(group, rand.randint(14, 39), rand.randint(13, 36), "*")
                if task.question not in seen:
                    seen.add(task.question)
                    result.append(task)
                    break
            else:
                raise ValueError("could not generate a unique heldout task")
    rand.shuffle(result)
    return result


def infer(task: Task) -> dict:
    payload = {
        "model": MODEL,
        "messages": [{"role":"system","content":PROMPT},
                     {"role":"user","content":task.question}],
        "stream": False, "think": False,
        "options": {"temperature":0, "num_predict":48},
        "keep_alive": "2m",
    }
    request = Request(URL, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type":"application/json"}, method="POST")
    before = time.perf_counter()
    with urlopen(request, timeout=75) as reply:
        response = json.load(reply)
    elapsed = round(time.perf_counter()-before, 4)
    if response.get("model") != MODEL or not response.get("done"):
        raise RuntimeError("local model response is not from the pinned requested identity")
    body = str(response.get("message", {}).get("content", "")).strip()
    number = int(body) if RX.fullmatch(body) else None
    return {"answer": number, "response_valid": number is not None,
            "model_correct": number == task.correct, "seconds": elapsed}


def calculate_arithmetic(task: Task) -> int:
    """Execute a local integer calculator (separate from Task.correct)."""
    if task.operation == "+":
        return sum((task.left, task.right))
    if task.operation == "*":
        return task.left.__mul__(task.right)
    raise ValueError("unsupported arithmetic verifier operation")


def execute_choice(task: Task, model_result: dict, action: str, *,
                   verifier=None) -> dict:
    """Report an executed action, never infer verification success by fiat.

    The optional verifier injection is only for deterministic failure tests;
    production trial calls the local integer calculator explicitly.
    """
    if action not in ("ANSWER", "VERIFY"):
        raise ValueError("unsupported action")
    if type(model_result) is not dict or "answer" not in model_result:
        raise ValueError("model result missing answer")
    original = model_result["answer"]
    if original is not None and type(original) is not int:
        raise TypeError("model answer must be a plain integer or None")
    if action == "ANSWER":
        return {
            "verification_executed": False,
            "verification_seconds": None,
            "final_answer": original,
            "learned_correct": original == task.correct,
            "unnecessary_verify": False,
        }
    calculator = calculate_arithmetic if verifier is None else verifier
    if not callable(calculator):
        raise TypeError("verifier must be callable")
    started = time.perf_counter()
    checked = calculator(task)
    elapsed = time.perf_counter() - started
    if type(checked) is not int:
        raise TypeError("verifier must return a plain integer")
    return {
        "verification_executed": True,
        "verification_seconds": elapsed,
        "final_answer": checked,
        "learned_correct": checked == task.correct,
        "unnecessary_verify": original == task.correct,
    }


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="explicitly run local model")
    parser.add_argument("--train-seed", type=int, default=1111,
                        help="frozen synthetic public training question seed")
    parser.add_argument("--holdout-seed", type=int, default=54122,
                        help="frozen synthetic public holdout question seed")
    parser.add_argument("--output", type=Path, required=True, help="local private receipt")
    args=parser.parse_args()
    if not args.execute:
        parser.error("requires --execute for real local inference")
    out=args.output.resolve()
    # Keep private experiments outside tracked Git worktrees.
    if "bt2-vera-adaptive-choice-20261121-private-receipts" not in out.parts:
        parser.error("output must reside in private fixed receipt directory")
    if out.exists():
        parser.error("never overwrite an earlier receipt")
    training = tasks(args.train_seed, 12)
    heldout = tasks(args.holdout_seed, 10,
                    excluded={task.question for task in training})
    probe = AdaptiveChoiceProbe()
    initial = [probe.choose(t.context) for t in heldout]
    training_results = []
    for i, task in enumerate(training):
        result = infer(task)
        training_results.append({"group": task.group, "question": task.question,
                                 "expected_answer": task.correct, **result})
        # The outcome of the actually run model compared with independently
        # computed arithmetic decides which route has higher utility.
        target = "ANSWER" if result["model_correct"] else "VERIFY"
        for action in ("ANSWER", "VERIFY"):
            probe.observe(task.context, action, action == target,
                          f"measured-{i}-{action}")
        print(f"TRAIN {i+1}/{len(training)} {task.group} model_correct={result['model_correct']}",
              flush=True)
    probe.consolidate(epochs=40)
    changed = [probe.choose(t.context) for t in heldout]
    outcome = []
    for i, task in enumerate(heldout):
        result = infer(task)
        observed = execute_choice(task, result, changed[i])
        outcome.append({
            "group": task.group, "question": task.question,
            "expected_answer": task.correct, **result,
            "baseline_action": initial[i], "learned_action": changed[i],
            "baseline_correct": result["model_correct"], **observed,
        })
        print(f"HELDOUT {i+1}/{len(heldout)} {task.group} model_correct={result['model_correct']}",
              flush=True)
    stats = {
        "model":MODEL,
        "training_tasks":len(training),
        "heldout_tasks":len(heldout),
        "baseline_accuracy":sum(e["baseline_correct"] for e in outcome)/len(outcome),
        "learned_accuracy":sum(e["learned_correct"] for e in outcome)/len(outcome),
        "verify_fraction":sum(e["learned_action"]=="VERIFY" for e in outcome)/len(outcome),
        "verification_executions":sum(e["verification_executed"] for e in outcome),
        "measured_verifier_seconds":sum(e["verification_seconds"] or 0.0 for e in outcome),
        "unnecessary_verifies":sum(e["unnecessary_verify"] for e in outcome),
        "baseline_utility":sum(1.0 if e["baseline_correct"] else 0.0 for e in outcome)/len(outcome),
        "learned_utility":sum((1 if e["learned_correct"] else 0) -
                              (.24 if e["learned_action"]=="VERIFY" else 0)
                              for e in outcome)/len(outcome),
        "updates":probe.updates,
        "consolidation_epochs":probe.consolidation_epochs,
        "weight_norm":probe.weight_norm,
    }
    record={"schema":"LOCAL_VERA_ARITHMETIC_FEEDBACK_TRIAL_SOURCE_ONLY_V1",
            "source":"loopback-local-model-plus-independent-python-integer-oracle",
            "feedback_source":"OBSERVED_LOCAL_MODEL_AND_DETERMINISTIC_ORACLE",
            "train_seed":args.train_seed,"holdout_seed":args.holdout_seed,
            "model_cognition":"NOT_QUALIFIED","self_authorship":"NOT_ESTABLISHED",
            "training":training_results,"holdout":outcome,"stats":stats,
            "learner_snapshot":probe.snapshot()}
    out.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(record,sort_keys=True,indent=2,allow_nan=False)
    out.write_text(serialized,encoding="utf-8")
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    (out.with_suffix(out.suffix+".sha256")).write_text(digest+"  "+out.name+"\n",encoding="utf-8")
    # Reconstruct in a new object; the caller can also replay in a fresh process.
    loaded=AdaptiveChoiceProbe.from_snapshot(json.loads(out.read_text(encoding="utf-8"))["learner_snapshot"])
    assert loaded.snapshot()==probe.snapshot()
    print("SUMMARY="+json.dumps(stats,sort_keys=True),flush=True)
    print("RECEIPT_SHA256="+digest,flush=True)
    print("OUTPUT="+str(out),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
