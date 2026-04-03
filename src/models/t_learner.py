from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .base import UpliftModel


def _make_pipeline(frame: pd.DataFrame) -> Pipeline:
    categorical = list(frame.select_dtypes(include=["object", "category", "bool"]).columns)
    numeric = [c for c in frame.columns if c not in categorical]
    pre = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical), ("num", "passthrough", numeric)]
    )
    return Pipeline([("pre", pre), ("clf", HistGradientBoostingClassifier(max_depth=6, random_state=42))])


class TLearner(UpliftModel):
    def __init__(self) -> None:
        self.treat_model: Pipeline | None = None
        self.ctrl_model: Pipeline | None = None

    def fit(self, x: pd.DataFrame, treatment: pd.Series, target: pd.Series) -> "TLearner":
        t_mask = treatment == 1
        c_mask = treatment == 0
        self.treat_model = _make_pipeline(x)
        self.ctrl_model = _make_pipeline(x)
        self.treat_model.fit(x[t_mask], target[t_mask])
        self.ctrl_model.fit(x[c_mask], target[c_mask])
        return self

    def predict_uplift(self, x: pd.DataFrame) -> pd.Series:
        if self.treat_model is None or self.ctrl_model is None:
            raise RuntimeError("Model not fitted")
        p1 = self.treat_model.predict_proba(x)[:, 1]
        p0 = self.ctrl_model.predict_proba(x)[:, 1]
        return pd.Series(p1 - p0, index=x.index)
