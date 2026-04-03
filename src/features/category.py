from __future__ import annotations

import numpy as np
import pandas as pd


def build_category_features(purchases: pd.DataFrame, products: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if purchases.empty:
        return pd.DataFrame(columns=["client_id"])

    merged = purchases.merge(products[["product_id", "level_2"]], on="product_id", how="left")
    merged["level_2"] = merged["level_2"].fillna("unknown")

    cat_spend = (
        merged.groupby(["client_id", "level_2"], as_index=False)["trn_sum_from_iss"]
        .sum()
        .rename(columns={"trn_sum_from_iss": "category_spend"})
    )
    total_spend = cat_spend.groupby("client_id", as_index=False)["category_spend"].sum().rename(
        columns={"category_spend": "total_spend"}
    )
    cat_spend = cat_spend.merge(total_spend, on="client_id", how="left")
    cat_spend["share"] = cat_spend["category_spend"] / cat_spend["total_spend"].replace(0, 1)

    entropy = cat_spend.groupby("client_id")["share"].apply(lambda s: float(-(s * np.log(s + 1e-12)).sum()))
    breadth = cat_spend.groupby("client_id")["level_2"].nunique().rename("n_unique_categories")
    top_share = cat_spend.groupby("client_id")["share"].max().rename("top_category_share")

    top_categories = (
        cat_spend.groupby("level_2")["category_spend"].sum().sort_values(ascending=False).head(top_n).index
    )
    piv = (
        cat_spend[cat_spend["level_2"].isin(top_categories)]
        .pivot(index="client_id", columns="level_2", values="share")
        .fillna(0)
    )
    piv.columns = [f"category_share_{c}" for c in piv.columns]

    result = pd.concat([breadth, top_share, entropy.rename("category_entropy"), piv], axis=1).reset_index()
    return result
