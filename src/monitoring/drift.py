from __future__ import annotations

import numpy as np
import pandas as pd


def population_stability_index(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    expected = expected.astype(float)
    actual = actual.astype(float)
    quantiles = np.linspace(0, 1, bins + 1)
    cuts = np.unique(np.quantile(expected, quantiles))
    if len(cuts) <= 2:
        return 0.0

    exp_hist, _ = np.histogram(expected, bins=cuts)
    act_hist, _ = np.histogram(actual, bins=cuts)
    exp_ratio = np.clip(exp_hist / max(exp_hist.sum(), 1), 1e-6, None)
    act_ratio = np.clip(act_hist / max(act_hist.sum(), 1), 1e-6, None)
    return float(((act_ratio - exp_ratio) * np.log(act_ratio / exp_ratio)).sum())
