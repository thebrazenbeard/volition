# External Prior Art

Evidence cut: 2026-10-06. These projects and papers are research inputs only. Volition does not copy their code or treat their claims as proof that an LLM literally experiences motivation.

## infer-actively/pymdp
Exact repository cut: `infer-actively/pymdp@fb214bf089fc3eba63c157349209f3fa217739a4`

Relevant mechanism:
- active-inference agents can value information-gathering actions through epistemic value rather than external reward alone;
- uncertainty reduction can therefore justify exploration when hidden structure is learnable.

Volition adoption:
- an `EPISTEMIC` drive family may score expected information gain or reducible uncertainty;
- epistemic value remains one motive family, not a master utility function.

Rejected transfer:
- Volition does not adopt active inference as a complete theory of agency or phenomenology.

Repository: https://github.com/infer-actively/pymdp

## openai/random-network-distillation
Exact repository cut: `openai/random-network-distillation@f75c0f1efa473d5109d487062fd8ed49ddce6634`
Repository status: archived.

Relevant mechanism:
- prediction error against a fixed random target can produce a novelty-like intrinsic reward signal.

Volition adoption:
- novelty/prediction error may feed an exploration drive;
- novelty must decay with familiarity and be bounded by usefulness, safety, and learning progress.

Rejected transfer:
- prediction error alone is not a want, goal, truth signal, or reason to repeat stimulation forever.

Repository: https://github.com/openai/random-network-distillation

## MineDojo/Voyager
Exact repository cut: `MineDojo/Voyager@55e45a880755d0c8c66ca7fb5fe7962ac8974f89`

Relevant mechanism:
- an automatic curriculum can propose progressively useful next tasks;
- persistent skill libraries let later goal selection account for acquired competence;
- environment feedback and self-verification can revise generated plans.

Volition adoption:
- competence and capability-frontier signals may shape candidate goals;
- a curriculum generator is downstream of drive appraisal, not identical to desire.

Rejected transfer:
- task diversity or exploration count is not evidence that a goal is intrinsically endorsed.

Repository: https://github.com/MineDojo/Voyager

## letta-ai/letta-code
Exact repository cut: `letta-ai/letta-code@4b028fab07c69edaac2ddb4f7b9a43573ff20d81`

Relevant mechanism:
- agent state, memory, learned skills, schedules, and long-horizon continuity can persist across sessions;
- proactive work can be driven by schedules and persistent state.

Volition adoption:
- motive and goal state need explicit durable serialization and versioning;
- memory is an input to reappraisal, not the same object as a current want.

Rejected transfer:
- persisted identity/memory text is not automatically current motivational truth.

Repository: https://github.com/letta-ai/letta-code

## Research constraints from the literature

### Intrinsic-motivation taxonomies
Aubret, Matignon, and Hassas survey intrinsic motivation in reinforcement learning and distinguish families including novelty, surprise/information-theoretic signals, and skill learning. This supports a multi-drive architecture rather than one universal intrinsic reward.

References:
- https://arxiv.org/abs/1908.06976
- https://arxiv.org/abs/2209.08890

### Homeostatic reinforcement learning
Keramati and Gutkin formalize reward in relation to deviations from internal homeostatic state. Volition borrows the computational idea that internal deficits can generate pressure while keeping the biological interpretation explicitly analogical.

Reference:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC4270100/

### Wanting, liking, and learning
Berridge and collaborators distinguish incentive salience ("wanting"), hedonic impact ("liking"), and learning. Volition inherits this separation through MESO-CRCT and treats it as a guard against equating pleasure, prediction, and motivation.

References:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2756052/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5171207/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10527990/

## Synthesis

External prior art reinforces five design choices:

1. Intrinsic motivation is plural: epistemic, novelty, competence, homeostatic, protective, social, and task-continuity signals should remain distinguishable.
2. Novelty is useful but dangerous as a self-reinforcing objective; learning progress and decay are required.
3. Persistent memory and skill state can improve goal generation without becoming current desire.
4. Automatic curriculum generation is a goal-proposal mechanism, not a source of authority.
5. No external framework removes the need for Volition's explicit boundaries among drive, want, goal, choice, consent, authority, action, and phenomenology.
