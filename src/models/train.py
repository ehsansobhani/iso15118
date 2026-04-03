from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .evaluate import auuc
from .s_learner import SLearner
from .t_learner import TLearner
from .x_learner import XLearner


@dataclass
class TrainResult:
    model_name: str
    model: object
    validation_auuc: float


def train_and_select(x: pd.DataFrame, treatment: pd.Series, target: pd.Series) -> TrainResult:
    candidates = {"s_learner": SLearner(), "t_learner": TLearner(), "x_learner": XLearner()}
    best: TrainResult | None = None

    for name, model in candidates.items():
        fitted = model.fit(x, treatment, target)
        score = auuc(target, treatment, fitted.predict_uplift(x))
        result = TrainResult(model_name=name, model=fitted, validation_auuc=score)
        if best is None or result.validation_auuc > best.validation_auuc:
            best = result

    return best
