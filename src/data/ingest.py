from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_x5_dataset(base_dir: str | Path) -> dict[str, pd.DataFrame]:
    base = Path(base_dir)
    return {
        "clients": load_csv(base / "clients.csv"),
        "products": load_csv(base / "products.csv"),
        "purchases": load_csv(base / "purchases.csv"),
        "uplift_train": load_csv(base / "uplift_train.csv"),
    }
