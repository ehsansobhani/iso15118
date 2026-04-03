from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression

from .base import UpliftModel
from .t_learner import TLearner


class XLearner(UpliftModel):
    """Practical X-learner variant using T-learner predictions + propensity weighting."""

    def __init__(self) -> None:
        self.t_learner = TLearner()
        self.propensity_model = LogisticRegression(max_iter=1000)

    def fit(self, x: pd.DataFrame, treatment: pd.Series, target: pd.Series) -> "XLearner":
        self.t_learner.fit(x, treatment, target)
        x_enc = pd.get_dummies(x, drop_first=False)
        self.propensity_model.fit(x_enc, treatment)
        self._x_columns = list(x_enc.columns)
        return self

    def predict_uplift(self, x: pd.DataFrame) -> pd.Series:
        base_tau = self.t_learner.predict_uplift(x)
        x_enc = pd.get_dummies(x, drop_first=False).reindex(columns=self._x_columns, fill_value=0)
        propensity = self.propensity_model.predict_proba(x_enc)[:, 1]
        weight = pd.Series(propensity, index=x.index)
        return base_tau * (0.5 + (weight - 0.5).abs())
