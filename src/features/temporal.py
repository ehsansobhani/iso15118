from __future__ import annotations

import numpy as np
import pandas as pd


def build_temporal_features(purchases: pd.DataFrame) -> pd.DataFrame:
    if purchases.empty:
        return pd.DataFrame(columns=["client_id"])

    df = purchases.copy()
    df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"])
    df["dow"] = df["transaction_datetime"].dt.dayofweek
    df["hour"] = df["transaction_datetime"].dt.hour

    grouped = df.groupby("client_id")
    preferred_dow = grouped["dow"].agg(lambda x: int(x.mode().iloc[0])).rename("preferred_day_of_week")
    preferred_hour = grouped["hour"].agg(lambda x: int(x.mode().iloc[0])).rename("preferred_hour")
    weekend_ratio = grouped["dow"].apply(lambda x: float((x >= 5).mean())).rename("weekend_ratio")

    def regularity(series: pd.Series) -> float:
        dates = series.sort_values().drop_duplicates()
        if len(dates) < 3:
            return 0.0
        diffs = dates.diff().dt.days.dropna()
        return float(diffs.std() / max(diffs.mean(), 1e-9))

    regularity_cv = grouped["transaction_datetime"].apply(regularity).rename("purchase_regularity")
    out = pd.concat([preferred_dow, preferred_hour, weekend_ratio, regularity_cv], axis=1).reset_index()
    out["is_weekend_shopper"] = (out["weekend_ratio"] > 0.5).astype(int)
    return out.drop(columns=["weekend_ratio"])
