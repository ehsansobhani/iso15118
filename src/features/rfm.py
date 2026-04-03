from __future__ import annotations

import pandas as pd


def build_rfm_features(purchases: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Build customer-level RFM + loyalty redemption features."""
    if purchases.empty:
        return pd.DataFrame(columns=["client_id"])

    df = purchases.copy()
    df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"])
    if snapshot_date is None:
        snapshot_date = df["transaction_datetime"].max().normalize()

    group = df.groupby("client_id", as_index=False)
    last_purchase = group["transaction_datetime"].max().rename(columns={"transaction_datetime": "last_purchase"})
    tx_counts = group["transaction_id"].nunique().rename(columns={"transaction_id": "frequency_total"})
    monetary = group["trn_sum_from_iss"].agg(["sum", "mean", "std"]).reset_index()
    monetary.columns = ["client_id", "monetary_total", "monetary_avg_basket", "monetary_std_basket"]

    lookback_30d = df[df["transaction_datetime"] >= snapshot_date - pd.Timedelta(days=30)]
    freq_30d = lookback_30d.groupby("client_id", as_index=False)["transaction_id"].nunique().rename(
        columns={"transaction_id": "frequency_30d"}
    )

    redemption = group[["trn_sum_from_red", "trn_sum_from_iss"]].sum()
    redemption["redemption_ratio"] = redemption["trn_sum_from_red"] / redemption["trn_sum_from_iss"].replace(0, 1)
    redemption = redemption[["client_id", "redemption_ratio"]]

    out = last_purchase.merge(tx_counts, on="client_id", how="left")
    out = out.merge(monetary, on="client_id", how="left")
    out = out.merge(freq_30d, on="client_id", how="left")
    out = out.merge(redemption, on="client_id", how="left")
    out["recency_days"] = (snapshot_date - out["last_purchase"].dt.normalize()).dt.days
    out = out.drop(columns=["last_purchase"])
    return out.fillna({"frequency_30d": 0, "monetary_std_basket": 0.0, "redemption_ratio": 0.0})
