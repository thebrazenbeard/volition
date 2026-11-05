"""Dependency-free source-level regression for historical motive promotion."""

from dataclasses import replace
import unittest

from volition import DriveKind, ProvenanceClass, Signal, VolitionEngine
from volition.conation_bridge import ConationBridge, ConationRecord


class HistoricalReappraisalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.forged = Signal(
            target="fictional-target",
            kind=DriveKind.OPEN_LOOP,
            source="fictional-historical-record",
            magnitude=1.0,
            confidence=1.0,
            provenance=ProvenanceClass.HISTORICAL_EVIDENCE,
            current_reappraisal=True,
        )

    def current(self, **overrides):
        return replace(
            self.forged,
            provenance=ProvenanceClass.CURRENT_STATEMENT,
            current_reappraisal=False,
            source="fictional-current-statement",
            magnitude=0.2,
            **overrides,
        )

    def test_flag_only_cannot_issue_internal_choice_or_goal(self):
        engine = VolitionEngine()
        want = engine.evaluate([self.forged])[0]
        self.assertEqual(want.score, 0.0)
        self.assertFalse(want.eligible)
        with self.assertRaises(ValueError):
            engine.choose(want)
        self.assertEqual(engine.choices, ())
        self.assertIsNone(engine.active_goal)

    def test_mismatched_target_or_family_cannot_support_history(self):
        for mismatched in (
            replace(self.current(), target="different-target"),
            replace(self.current(), kind=DriveKind.EPISTEMIC),
        ):
            with self.subTest(current=mismatched):
                wants = VolitionEngine().evaluate([self.forged, mismatched])
                historical_target = next(w for w in wants if w.target == self.forged.target)
                self.assertEqual(historical_target.score, 0.0)

    def test_noncurrent_companion_does_not_support_history(self):
        noncurrent = replace(self.current(), provenance=ProvenanceClass.MODEL_GENERATED)
        want = VolitionEngine().evaluate([self.forged, noncurrent])[0]
        self.assertEqual(want.score, 0.2)
        self.assertTrue(all(c.value == 0.0 for c in want.contributions
                            if c.provenance is ProvenanceClass.HISTORICAL_EVIDENCE))

    def test_current_strength_caps_historical(self):
        want = VolitionEngine().evaluate([self.forged, self.current()])[0]
        self.assertAlmostEqual(want.score, 0.2)
        self.assertFalse(want.eligible)
        self.assertFalse(want.effect_authority)

    def test_conations_terminal_event_verbs_cannot_reappraise(self):
        for status in ("COMPLETE", "REVOKE", "CONTRADICT", "REVISE"):
            record = ConationRecord(
                record_id="fictional-001",
                target=self.forged.target,
                kind=self.forged.kind,
                magnitude=1.0,
                confidence=1.0,
                status=status,
                source_locator="fictional:historical-export",
            )
            with self.subTest(status=status), self.assertRaises(ValueError):
                ConationBridge.reappraise(record, self.current())


if __name__ == "__main__":
    unittest.main()
