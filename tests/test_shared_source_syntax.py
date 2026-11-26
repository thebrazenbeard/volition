import unittest
from volition.current_readback import HostEvent, HostEventGateway
from volition.models import DriveKind, ProvenanceClass
from volition.operational_drive import ModelWantProposal, OperationalMotivation

class SharedSourceSyntax(unittest.TestCase):
    def test_invisible_host_source_fields_rejected(self):
        for field in ("source_ref", "evidence_id", "verifier_id"):
            for bad in ("\u200b", "unspecified\u200b", "\u093e"):
                with self.subTest(field=field, bad=ascii(bad)):
                    kwargs = dict(evidence_id="synthetic-1", payload=b"fictional",
                                  target="fictional target", kind=DriveKind.EPISTEMIC,
                                  magnitude=.8, confidence=1., source_ref="host:fictional",
                                  provenance=ProvenanceClass.CURRENT_OBSERVATION)
                    verifier = "synthetic-host"
                    if field == "verifier_id":
                        verifier = bad
                    else:
                        kwargs[field] = bad
                    with self.assertRaises(ValueError):
                        item = HostEvent(**kwargs)
                        HostEventGateway(lambda _: item, verifier_id=verifier).admit(item.evidence_id)

    def test_multilingual_source_preserves_exact_label_and_no_effect_authority(self):
        for label in ("host:caf\u00e9", "\u0915\u093e"):
            item = HostEvent("synthetic-1", b"fictional", "fictional target",
                             DriveKind.EPISTEMIC, .8, 1., label,
                             ProvenanceClass.CURRENT_OBSERVATION)
            a = HostEventGateway(lambda _: item, verifier_id="synthetic-host").admit(item.evidence_id)
            self.assertEqual(a.claim.source_ref, label)
            g = OperationalMotivation().propose(
                ModelWantProposal("p1", item.target, item.kind, item.evidence_id, "fictional"), a)
            self.assertIsNotNone(g)
            self.assertFalse(g.effect_authority)
