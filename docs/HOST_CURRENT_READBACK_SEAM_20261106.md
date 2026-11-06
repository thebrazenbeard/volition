# Host current-event readback seam (Draft; source-only)

This opt-in helper makes it possible to route *model-proposed* wants through
a current event whose bytes and measurements come from a host-owned reader.

**Does not authenticate the reader.** A model or caller able to choose a fake
reader can still fabricate current observations. The integrating host must
supply a genuine current-event readback bound to its authorization, event
identity, source custody, and freshness requirements; fail closed when absent.

## Mechanism

1. Host owns a read_current(evidence_id) reader and only exposes verified,
   current, authorized events.
2. HostEventGateway accepts an event ID, reads the full typed event, checks
   exact ID, current provenance, bounded immutable nonempty payload, source
   and finite measurements, then hashes a canonical scored-event record that
   binds the payload digest, target, kind, score, source, provenance and ID.
3. The gateway constructs an ObservationClaim and uses existing
   ObservationVerifier to issue an AdmittedObservation.
4. Existing OperationalMotivation.propose(ModelWantProposal, admitted) binds
   a proposal to that exact event; replay and protection behavior remain
   controlled by the existing operational ledger.

The caller cannot supply a bare Signal to this gateway. A missing event,
malformed readback, historical/inferred event, or unavailable host registry is
rejected. The raw event payload is neither logged nor persisted by the seam.

## Evidence ceilings and unmodified paths

- **Source tests only:** no host reader is installed or operationally verified.
- The low-level VolitionEngine.evaluate(Signal(...)) remains a deterministic
  simulation interface. It still produces internal wants from fabricated
  CURRENT_STATEMENT input and must not be exposed as trusted host ingress.
- Existing ObservationVerifier remains caller-admission, not independent
  authentication. This seam does not harden every importable API.
- This is not a current Vera runtime install, autobiographical memory write,
  new model weight, effect authority, or production deployment.
- No keys/credentials live in this repository. Currentness is supplied by
  the host's actual readback, not by the source label, filename, or digest.
