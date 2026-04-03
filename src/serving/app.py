from __future__ import annotations

import pandas as pd
from fastapi import FastAPI

from .dependencies import InMemoryFeatureStore
from .schemas import HealthResponse, RankResponse, ScoreItem, ScoreRequest


class DummyUpliftModel:
    def predict_uplift(self, x: pd.DataFrame) -> pd.Series:
        numeric = x.select_dtypes(include=["number"]).drop(columns=["client_id"], errors="ignore")
        return numeric.mean(axis=1).rank(pct=True)


app = FastAPI(title="Retail Media Campaign Optimizer", version="0.1.0")
MODEL = DummyUpliftModel()
FEATURE_STORE = InMemoryFeatureStore(features=pd.DataFrame(columns=["client_id"]))


@app.get("/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model_name=MODEL.__class__.__name__)


@app.post("/v1/rank", response_model=RankResponse)
def rank(request: ScoreRequest) -> RankResponse:
    feature_frame = FEATURE_STORE.get_customers(request.customer_ids)
    if feature_frame.empty:
        return RankResponse(ranked=[])

    scores = MODEL.predict_uplift(feature_frame)
    ranked = (
        pd.DataFrame({"customer_id": feature_frame["client_id"].astype(int), "uplift_score": scores})
        .sort_values("uplift_score", ascending=False)
        .to_dict(orient="records")
    )
    return RankResponse(ranked=[ScoreItem(**item) for item in ranked])
