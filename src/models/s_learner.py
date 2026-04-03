from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .base import UpliftModel


class SLearner(UpliftModel):
    def __init__(self) -> None:
        self.model: Pipeline | None = None
        self.features: list[str] = []

    def fit(self, x: pd.DataFrame, treatment: pd.Series, target: pd.Series) -> "SLearner":
        train = x.copy()
        train["treatment_flg"] = treatment.astype(int)
        self.features = list(train.columns)

        categorical = list(train.select_dtypes(include=["object", "category", "bool"]).columns)
        numeric = [c for c in train.columns if c not in categorical]
        pre = ColumnTransformer(
            transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical), ("num", "passthrough", numeric)]
        )
        self.model = Pipeline([("pre", pre), ("clf", HistGradientBoostingClassifier(max_depth=6, random_state=42))])
        self.model.fit(train, target)
        return self

    def predict_uplift(self, x: pd.DataFrame) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Model not fitted")
        treated = x.copy()
        control = x.copy()
        treated["treatment_flg"] = 1
        control["treatment_flg"] = 0
        p1 = self.model.predict_proba(treated)[:, 1]
        p0 = self.model.predict_proba(control)[:, 1]
        return pd.Series(p1 - p0, index=x.index)
