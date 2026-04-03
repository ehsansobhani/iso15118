from __future__ import annotations

import numpy as np
import pandas as pd

from .incrementality import IncrementalityMetrics, compute_incrementality


def run_ab_test(
    uplift_scores: pd.Series,
    observed_target: pd.Series,
    budget_pct: float = 0.30,
    seed: int = 42,
) -> dict[str, IncrementalityMetrics]:
    rng = np.random.default_rng(seed)
    n = len(uplift_scores)
    k = max(1, int(n * budget_pct))

    model_assignment = pd.Series(0, index=uplift_scores.index)
    model_assignment.loc[uplift_scores.sort_values(ascending=False).head(k).index] = 1

    random_assignment = pd.Series(rng.choice([0, 1], size=n, p=[1 - budget_pct, budget_pct]), index=uplift_scores.index)

    return {
        "model_targeting": compute_incrementality(observed_target, model_assignment),
        "random_targeting": compute_incrementality(observed_target, random_assignment),
    }
