"""Bounded operational appraisal expiry, not observation authentication."""
import json
import unittest
from hashlib import sha256
from volition import (ChoiceClass, DriveKind, GoalCompletionClaim, GoalCompletionVerifier,
    ModelWantProposal, ObservationClaim, ObservationVerifier, OperationalMotivation,
    Policy, ProvenanceClass, VolitionEngine)


def fresh(loop, i, target="A", magnitude=.8, kind=DriveKind.COMPETENCE):
    claim=ObservationClaim(i, "sha256:"+sha256(i.encode()).hexdigest(),
        target, kind, magnitude, 1., "fixture:external")
    admitted=ObservationVerifier([claim], verifier_id="fixture").admit(claim)
    proposal=None if kind is DriveKind.PROTECTION else ModelWantProposal(
        "p-"+i,target,kind,i,"bounded fixture")
    return proposal, admitted


def propose(loop,i,target="A",magnitude=.8):
    return loop.propose(*fresh(loop,i,target,magnitude))


def restore(loop):
    return OperationalMotivation.from_snapshot(json.loads(json.dumps(loop.snapshot())))


def receipt(goal):
    claim=GoalCompletionClaim("outcome",goal.goal_id,goal.choice_id,goal.revision,
        goal.target,"result","evidence","fixture:external",ProvenanceClass.CURRENT_OBSERVATION)
    return GoalCompletionVerifier([claim],verifier_id="fixture").admit(claim)


class OperationalFreshnessTests(unittest.TestCase):
    def test_no_new_evidence_expires_at_boundary(self):
        loop=OperationalMotivation()
        g=propose(loop,"initial")
        horizon=loop.engine.policy.goal_reappraisal_seconds
        loop.advance(horizon-1)
        self.assertEqual(loop.engine.active_goal,g)
        self.assertIsNotNone(loop.request_cognition())
        loop.advance(1)
        self.assertIsNone(loop.engine.active_goal)
        self.assertIsNone(loop.request_cognition())
        self.assertEqual(loop.engine.events[-1].kind,"GOAL_SUSPENDED")
        self.assertEqual(len(loop.engine.choices),1)

    def test_fresh_alternative_after_expiry(self):
        loop=OperationalMotivation()
        old=propose(loop,"a","A",.9)
        self.assertIsNone(propose(loop,"b-old","B",.6))
        loop.advance(loop.engine.policy.goal_reappraisal_seconds+1)
        self.assertIsNone(loop.engine.active_goal)
        self.assertIsNone(loop.request_cognition())
        self.assertEqual(len(loop.engine.choices),1)
        new=propose(loop,"b-new","B",.6)
        self.assertEqual(new.target,"B")
        self.assertNotEqual(new.goal_id,old.goal_id)
        self.assertIs(loop.engine.choices[-1].choice_class,ChoiceClass.MODEL_PROPOSED)

    def test_reappraisal_renews_anchor_and_cold_restores(self):
        loop=OperationalMotivation()
        old=propose(loop,"a")
        h=loop.engine.policy.goal_reappraisal_seconds
        loop.advance(h-1)
        new=propose(loop,"a-fresh",magnitude=.7)
        self.assertEqual(new.goal_id,old.goal_id)
        self.assertEqual(new.choice_id,old.choice_id)
        self.assertEqual(new.revision,old.revision+1)
        self.assertEqual(new.adopted_at_seconds,h-1)
        resumed=restore(loop)
        self.assertEqual(resumed.engine.active_goal,new)
        resumed.advance(1)
        self.assertEqual(resumed.engine.active_goal,new)
        self.assertIsNotNone(resumed.request_cognition())
        resumed.advance(h-1)
        self.assertIsNone(resumed.engine.active_goal)

    def test_replay_never_renews_and_fresh_old_target_reopens(self):
        loop=OperationalMotivation()
        p,a=fresh(loop,"a")
        old=loop.propose(p,a)
        h=loop.engine.policy.goal_reappraisal_seconds
        loop.advance(h-1)
        self.assertIsNone(loop.propose(p,a))
        self.assertEqual(loop.engine.active_goal,old)
        loop.advance(1)
        resumed=restore(loop)
        self.assertIsNone(resumed.engine.active_goal)
        self.assertIsNone(resumed.propose(p,a))
        self.assertIsNone(resumed.request_cognition())
        new=propose(resumed,"a-fresh")
        self.assertNotEqual(new.goal_id,old.goal_id)
        self.assertEqual(new.revision,1)

    def test_stale_legacy_snapshot_suspends_not_completes(self):
        loop=OperationalMotivation()
        old=propose(loop,"a")
        # Legacy producer advanced its engine but did not suspend.
        loop.engine.advance(loop.engine.policy.goal_reappraisal_seconds)
        resumed=restore(loop)
        self.assertIsNone(resumed.engine.active_goal)
        self.assertIsNone(resumed.request_cognition())
        with self.assertRaises(ValueError):
            resumed.complete(receipt(old))
        self.assertFalse(any(e.kind=="GOAL_COMPLETED" for e in resumed.engine.events))
        self.assertEqual(restore(resumed).snapshot(),resumed.snapshot())

    def test_direct_engine_clock_advance_guarded_before_proposal_and_request(self):
        for action in ("propose","request"):
            with self.subTest(action=action):
                loop=OperationalMotivation()
                propose(loop,"a",magnitude=.9)
                loop.engine.advance(loop.engine.policy.goal_reappraisal_seconds)
                if action=="propose":
                    new=propose(loop,"b","B",.6)
                    self.assertIsNotNone(new)
                    self.assertEqual(new.target,"B")
                else:
                    self.assertIsNone(loop.request_cognition())
                    self.assertIsNone(loop.engine.active_goal)

    def test_completion_replay_and_protection_survive_expiry(self):
        loop=OperationalMotivation()
        g=propose(loop,"a")
        r=receipt(g)
        self.assertTrue(loop.complete(r))
        loop.advance(loop.engine.policy.goal_reappraisal_seconds)
        self.assertFalse(restore(loop).complete(r))
        new=propose(loop,"new-a")
        self.assertNotEqual(new.goal_id,g.goal_id)
        _,danger=fresh(loop,"danger",kind=DriveKind.PROTECTION)
        self.assertTrue(loop.observe_protection(danger))
        loop.advance(loop.engine.policy.goal_reappraisal_seconds)
        resumed=restore(loop)
        self.assertIn("A",resumed.protection_latches)
        self.assertIsNone(propose(resumed,"blocked"))
        self.assertIsNone(resumed.request_cognition())
        _,safe=fresh(resumed,"clear",magnitude=0,kind=DriveKind.PROTECTION)
        self.assertTrue(resumed.clear_protection(safe))
        self.assertIsNotNone(propose(resumed,"new-after-clear"))

    def test_nonpositive_horizon_has_no_time_persistence(self):
        for horizon in (0,-1):
            with self.subTest(horizon=horizon):
                loop=OperationalMotivation(VolitionEngine(Policy(goal_reappraisal_seconds=horizon)))
                self.assertIsNotNone(propose(loop,"a"))
                self.assertIsNotNone(loop.request_cognition())
                loop.advance(.01)
                self.assertIsNone(loop.engine.active_goal)
                self.assertIsNone(loop.request_cognition())
                self.assertIsNotNone(propose(loop,"a-fresh"))


    def test_restore_revision_one_anchor_matches_adoption_receipt(self):
        loop=OperationalMotivation()
        loop.advance(17)
        g=propose(loop,"a")
        self.assertEqual(g.adopted_at_seconds,17)
        self.assertEqual(restore(loop).engine.active_goal,g)
        loop.engine.advance(loop.engine.policy.goal_reappraisal_seconds)
        snapshot=json.loads(json.dumps(loop.snapshot()))
        self.assertIsNone(OperationalMotivation.from_snapshot(snapshot).engine.active_goal)
        snapshot["engine"]["active_goal"]["adopted_at_seconds"]=loop.engine.elapsed_seconds
        with self.assertRaisesRegex(ValueError,"adoption.*time|adoption.*anchor"):
            OperationalMotivation.from_snapshot(snapshot)

    def test_completion_checks_expiry_after_direct_clock_advance(self):
        loop=OperationalMotivation()
        g=propose(loop,"a")
        loop.engine.advance(loop.engine.policy.goal_reappraisal_seconds)
        with self.assertRaises(ValueError):
            loop.complete(receipt(g))
        self.assertIsNone(loop.engine.active_goal)
        self.assertFalse(any(e.kind=="GOAL_COMPLETED" for e in loop.engine.events))
        self.assertIsNone(restore(loop).engine.active_goal)

    def test_historical_completion_replay_does_not_credit_expired_successor(self):
        loop=OperationalMotivation()
        old=propose(loop,"a")
        r=receipt(old)
        self.assertTrue(loop.complete(r))
        successor=propose(loop,"b","B")
        self.assertNotEqual(successor.goal_id,old.goal_id)
        loop.engine.advance(loop.engine.policy.goal_reappraisal_seconds)
        self.assertFalse(loop.complete(r))
        self.assertIsNone(loop.engine.active_goal)
        self.assertEqual(sum(e.kind=="GOAL_COMPLETED" for e in loop.engine.events),1)
        self.assertFalse(restore(loop).complete(r))


if __name__=="__main__":
    unittest.main()
