import math

import pytest

from volition.engine import VolitionEngine
from volition.models import DriveKind, Signal


@pytest.mark.parametrize("magnitude", [math.nan, math.inf, -math.inf])
def test_nonfinite_motive_magnitude_must_not_be_admitted(magnitude):
    engine = VolitionEngine()
    with pytest.raises(ValueError, match="finite"):
        engine.evaluate([
            Signal(
                target="open-loop-task",
                kind=DriveKind.HOMEOSTATIC,
                magnitude=magnitude,
            )
        ])
    assert engine.active_goal is None
    assert engine.events == ()
