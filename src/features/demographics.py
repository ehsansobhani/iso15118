from __future__ import annotations

import pandas as pd


def build_demographic_features(clients: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> pd.DataFrame:
    if clients.empty:
        return pd.DataFrame(columns=["client_id"])

    out = clients.copy()
    out["gender"] = out.get("gender", "U").fillna("U")
    out["age_bin"] = pd.cut(
        out.get("age"),
        bins=[0, 24, 34, 44, 54, 64, 120],
        labels=["18_24", "25_34", "35_44", "45_54", "55_64", "65_plus"],
    ).astype(str)

    if "first_issue_date" in out.columns:
        out["first_issue_date"] = pd.to_datetime(out["first_issue_date"])
        snapshot = snapshot_date or out["first_issue_date"].max().normalize()
        out["client_tenure_days"] = (snapshot - out["first_issue_date"].dt.normalize()).dt.days
    else:
        out["client_tenure_days"] = 0

    out["location_cluster"] = out.get("region", "unknown").astype(str)
    return out[["client_id", "gender", "age_bin", "client_tenure_days", "location_cluster"]]
