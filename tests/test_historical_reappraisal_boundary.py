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

    def test_placeholder_current_sources_cannot_reappraise_history(self):
        record = ConationRecord(
            record_id="fictional-002",
            target=self.forged.target,
            kind=self.forged.kind,
            magnitude=1.0,
            confidence=1.0,
            status="PRESENT",
            source_locator="fictional:historical-export",
        )
        for placeholder in (
            "unspecified ", " unspecified ", "\tUnSpEcIfIeD\n", " ", "",
            "\u200b", "\ufeff", "\u2060", "\x00", "\u034f", "\ufe0f",
            "Unspecified\u200b", "UNSPECIFIED\ufeff", "Unsp\u034fecified",
            "current:\x00synthetic", "\u200bcurrent:synthetic",
        ):
            with self.subTest(source=repr(placeholder)), self.assertRaises(ValueError):
                ConationBridge.reappraise(record, replace(self.current(), source=placeholder))

    def test_explicit_unicode_current_identifiers_remain_admissible(self):
        record = ConationRecord(
            record_id="fictional-003", target=self.forged.target,
            kind=self.forged.kind, magnitude=0.8, confidence=0.8,
            status="PRESENT", source_locator="fictional:historical-export",
        )
        for named_source in (
            "café:révision", "観測:現在", "запись:источник", "e\u0301tude:record",
            "source:مراجعة", "source:χρόνος", "source:observed\u00a0now",
        ):
            with self.subTest(source=named_source):
                historical, current = ConationBridge.reappraise(
                    record, replace(self.current(), source=named_source)
                )
                self.assertTrue(historical.current_reappraisal)
                self.assertEqual(current.source, named_source)

    def test_raw_engine_rejects_invisible_or_control_source_syntax(self):
        for invisible in ("\u200b", "\ufeff", "\u2060", "\x00", "\u034f", "\ufe0f", "named\u200b"):
            with self.subTest(source=repr(invisible)), self.assertRaises(ValueError):
                VolitionEngine().evaluate([
                    self.forged,
                    replace(self.current(), source=invisible),
                ])

    def test_raw_engine_keeps_default_and_multilingual_source_compatibility(self):
        for source_id in ("unspecified", "source:café", "source:漢字", "source:e\u0301tude"):
            with self.subTest(source=source_id):
                want = VolitionEngine().evaluate([
                    replace(self.current(), source=source_id),
                ])[0]
                self.assertEqual(want.target, self.forged.target)


if __name__ == "__main__":
    unittest.main()
