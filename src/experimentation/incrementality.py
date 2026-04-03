from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class IncrementalityMetrics:
    ate: float
    incremental_conversions: float
    cost_per_incremental_conversion: float
    roi: float


def compute_incrementality(
    y: pd.Series,
    assignment: pd.Series,
    avg_order_value: float = 15.0,
    sms_cost: float = 0.04,
) -> IncrementalityMetrics:
    treat_rate = y[assignment == 1].mean()
    ctrl_rate = y[assignment == 0].mean()
    ate = float(treat_rate - ctrl_rate)
    targeted_n = int((assignment == 1).sum())
    incr = ate * targeted_n
    total_cost = targeted_n * sms_cost
    inc_revenue = incr * avg_order_value
    cpic = float(total_cost / incr) if incr > 0 else float("inf")
    roi = float((inc_revenue - total_cost) / total_cost) if total_cost > 0 else 0.0
    return IncrementalityMetrics(ate=ate, incremental_conversions=float(incr), cost_per_incremental_conversion=cpic, roi=roi)
