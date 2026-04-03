import pandas as pd

from features.pipeline import build_feature_matrix


def test_build_feature_matrix_has_core_columns() -> None:
    clients = pd.DataFrame({"client_id": [1, 2], "age": [30, 50], "gender": ["M", "F"]})
    products = pd.DataFrame({"product_id": [101, 102], "level_2": ["dairy", "bakery"]})
    purchases = pd.DataFrame(
        {
            "client_id": [1, 1, 2],
            "product_id": [101, 102, 101],
            "transaction_id": [10, 11, 20],
            "store_id": [1, 1, 2],
            "trn_sum_from_iss": [100, 60, 40],
            "trn_sum_from_red": [10, 0, 2],
            "transaction_datetime": ["2019-01-01", "2019-01-10", "2019-01-03"],
        }
    )

    feat = build_feature_matrix(clients, purchases, products)
    assert {"client_id", "recency_days", "n_unique_categories", "avg_items_per_basket"}.issubset(feat.columns)
