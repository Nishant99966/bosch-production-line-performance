import numpy as np
from bosch_pipeline.metrics import optimize_mcc_threshold

def test_optimize_mcc_threshold_finds_separating_cutoff():
    y = np.array([0, 0, 0, 1, 1, 1])
    p = np.array([0.01, 0.10, 0.20, 0.70, 0.80, 0.95])
    threshold, mcc = optimize_mcc_threshold(y, p)
    assert 0.2 < threshold <= 0.7
    assert mcc == 1.0
