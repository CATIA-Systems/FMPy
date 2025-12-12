from fmpy import simulate_fmu
import numpy as np


def test_variable_alias(reference_fmus_dist_dir):
    filename = reference_fmus_dist_dir / "3.0" / "BouncingBall.fmu"
    result = simulate_fmu(filename, output=["h", "h_ft"])
    assert np.all(result["h"] == result["h_ft"])
