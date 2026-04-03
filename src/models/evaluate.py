from __future__ import annotations

import numpy as np
import pandas as pd


def uplift_at_k(y: pd.Series, treatment: pd.Series, uplift_score: pd.Series, k: float = 0.3) -> float:
    n = max(1, int(len(y) * k))
    idx = uplift_score.sort_values(ascending=False).head(n).index
    yt, wt = y.loc[idx], treatment.loc[idx]
    treat_rate = yt[wt == 1].mean() if (wt == 1).any() else 0.0
    ctrl_rate = yt[wt == 0].mean() if (wt == 0).any() else 0.0
    return float(treat_rate - ctrl_rate)


def qini_curve(y: pd.Series, treatment: pd.Series, uplift_score: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame({"y": y, "w": treatment, "score": uplift_score}).sort_values("score", ascending=False)
    frame["n"] = np.arange(1, len(frame) + 1)
    frame["cum_treat_y"] = (frame["y"] * (frame["w"] == 1)).cumsum()
    frame["cum_ctrl_y"] = (frame["y"] * (frame["w"] == 0)).cumsum()
    frame["cum_treat_n"] = (frame["w"] == 1).cumsum().clip(lower=1)
    frame["cum_ctrl_n"] = (frame["w"] == 0).cumsum().clip(lower=1)
    frame["incremental"] = frame["cum_treat_y"] - frame["cum_ctrl_y"] * (frame["cum_treat_n"] / frame["cum_ctrl_n"])
    return frame[["n", "incremental"]]


def auuc(y: pd.Series, treatment: pd.Series, uplift_score: pd.Series) -> float:
    curve = qini_curve(y, treatment, uplift_score)
    return float(np.trapz(curve["incremental"], curve["n"]))
