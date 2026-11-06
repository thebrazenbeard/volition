"""Bounded source tests for a host-owned live-event readback seam."""

import unittest

from volition.current_readback import HostEvent, HostEventGateway
from volition.models import DriveKind, ProvenanceClass, Signal
from volition.operational_drive import ModelWantProposal, OperationalMotivation


def event(**updates):
    fields = {
        "evidence_id": "evt-1", "payload": b"public current pump observation",
        "target": "diagnose pump", "kind": DriveKind.EPISTEMIC,
        "magnitude": 0.8, "confidence": 1.0,
        "source_ref": "host:event:1",
        "provenance": ProvenanceClass.CURRENT_STATEMENT,
    }
    fields.update(updates)
    return HostEvent(**fields)


class ReadbackAdmissionTests(unittest.TestCase):
    def test_no_readback_denies_fabricated_current_signal(self):
        gate = HostEventGateway(lambda _: None, verifier_id="trusted-host-A")
        fabricated = Signal(target="diagnose pump", kind=DriveKind.EPISTEMIC,
                            magnitude=1, provenance=ProvenanceClass.CURRENT_STATEMENT)
        with self.assertRaises((TypeError, ValueError)):
            gate.admit(fabricated)
        with self.assertRaises(ValueError):
            gate.admit("evt-1")

    def test_exact_host_event_supplies_scored_operational_goal(self):
        item = event()
        gate = HostEventGateway(lambda key: item if key == "evt-1" else None,
                                verifier_id="trusted-host-A")
        admitted = gate.admit("evt-1")
        self.assertEqual(admitted.claim.magnitude, 0.8)
        self.assertEqual(admitted.claim.source_ref, "host:event:1")
        model = ModelWantProposal("proposal-1", item.target, item.kind,
                                  item.evidence_id, "bounded public reason")
        engine = OperationalMotivation()
        goal = engine.propose(model, admitted)
        self.assertIsNotNone(goal)
        self.assertFalse(goal.effect_authority)
        self.assertIsNone(engine.propose(model, admitted))

    def test_readback_must_match_requested_id(self):
        gate = HostEventGateway(lambda _: event(evidence_id="other"),
                                verifier_id="trusted-host-A")
        with self.assertRaises(ValueError):
            gate.admit("evt-1")


    def test_historical_or_inferred_event_fails_closed(self):
        for provenance in (ProvenanceClass.HISTORICAL_EVIDENCE,
                           ProvenanceClass.INFERENCE, ProvenanceClass.MODEL_GENERATED):
            item = event(provenance=provenance)
            gate = HostEventGateway(lambda _: item, verifier_id="trusted-host-A")
            with self.subTest(provenance=provenance), self.assertRaises(ValueError):
                gate.admit("evt-1")

    def test_untrusted_source_and_bad_payload_fails_closed(self):
        for item in (
            event(source_ref="unspecified"),
            event(source_ref="  "),
            event(payload=b""),
            event(payload=b"a" * 65537),
            event(payload="not bytes"),
            event(magnitude=True),
        ):
            gate = HostEventGateway(lambda _: item, verifier_id="trusted-host-A")
            with self.subTest(item=item), self.assertRaises(ValueError):
                gate.admit("evt-1")

    def test_readback_exception_is_typed_hold(self):
        def broken(_):
            raise OSError("host event registry unavailable")
        gate = HostEventGateway(broken, verifier_id="trusted-host-A")
        with self.assertRaises(ValueError):
            gate.admit("evt-1")

    def test_same_payload_changed_measurement_changes_claim_digest(self):
        one = event(magnitude=0.8)
        two = event(magnitude=0.4)
        first = HostEventGateway(lambda _: one, verifier_id="trusted-host-A").admit("evt-1")
        second = HostEventGateway(lambda _: two, verifier_id="trusted-host-A").admit("evt-1")
        self.assertNotEqual(first.claim.content_digest, second.claim.content_digest)

    def test_same_payload_changed_source_changes_claim_digest(self):
        one = event(source_ref="host:event:1")
        two = event(source_ref="host:event:2")
        first = HostEventGateway(lambda _: one, verifier_id="trusted-host-A").admit("evt-1")
        second = HostEventGateway(lambda _: two, verifier_id="trusted-host-A").admit("evt-1")
        self.assertNotEqual(first.claim.content_digest, second.claim.content_digest)


if __name__ == "__main__":
    unittest.main()
