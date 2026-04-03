from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class UpliftPrediction:
    client_id: pd.Series
    uplift_score: pd.Series


class UpliftModel:
    def fit(self, x: pd.DataFrame, treatment: pd.Series, target: pd.Series) -> "UpliftModel":
        raise NotImplementedError

    def predict_uplift(self, x: pd.DataFrame) -> pd.Series:
        raise NotImplementedError
