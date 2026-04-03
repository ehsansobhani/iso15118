from __future__ import annotations

import pandas as pd

from .basket import build_basket_features
from .category import build_category_features
from .demographics import build_demographic_features
from .rfm import build_rfm_features
from .temporal import build_temporal_features


def build_feature_matrix(
    clients: pd.DataFrame,
    purchases: pd.DataFrame,
    products: pd.DataFrame,
    snapshot_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Build unified customer-level features for uplift modeling."""
    demo = build_demographic_features(clients, snapshot_date=snapshot_date)
    rfm = build_rfm_features(purchases, snapshot_date=snapshot_date)
    cat = build_category_features(purchases, products)
    temporal = build_temporal_features(purchases)
    basket = build_basket_features(purchases)

    features = demo
    for frame in [rfm, cat, temporal, basket]:
        features = features.merge(frame, on="client_id", how="left")

    numeric = features.select_dtypes(include=["number"]).columns
    features[numeric] = features[numeric].fillna(0)
    features = features.fillna("unknown")
    return features
