from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class InMemoryFeatureStore:
    features: pd.DataFrame

    def get_customers(self, customer_ids: list[int]) -> pd.DataFrame:
        return self.features[self.features["client_id"].isin(customer_ids)].copy()
