from __future__ import annotations

import pandas as pd


def build_basket_features(purchases: pd.DataFrame) -> pd.DataFrame:
    if purchases.empty:
        return pd.DataFrame(columns=["client_id"])

    tx = (
        purchases.groupby(["client_id", "transaction_id", "store_id"], as_index=False)
        .agg(n_items=("product_id", "count"), n_unique_products=("product_id", "nunique"))
    )

    grouped = tx.groupby("client_id", as_index=False).agg(
        avg_items_per_basket=("n_items", "mean"),
        avg_unique_products=("n_unique_products", "mean"),
        n_unique_stores=("store_id", "nunique"),
        express_trip_ratio=("n_items", lambda x: float((x <= 5).mean())),
    )

    mode_store = tx.groupby("client_id")["store_id"].agg(lambda x: x.value_counts().iloc[0]).rename("max_store_visits")
    store_visits = tx.groupby("client_id")["store_id"].count().rename("total_store_visits")
    loyalty = (mode_store / store_visits).rename("store_loyalty")

    return grouped.merge(loyalty.reset_index(), on="client_id", how="left")
