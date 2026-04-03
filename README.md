# Retail Media Campaign Optimizer

End-to-end ML system for brand campaign targeting and incrementality measurement, inspired by the X5 RetailHero uplift dataset.

## What is implemented

- Data ingestion layer for X5-style CSV tables (`clients`, `products`, `purchases`, `uplift_train`).
- Production-oriented feature engineering pipeline:
  - RFM features
  - category affinity features
  - temporal behavior features
  - basket/store behavior features
  - demographic features
- Uplift modeling layer with three working learners:
  - S-Learner
  - T-Learner
  - X-Learner (propensity-weighted variant)
- Evaluation utilities:
  - Qini curve
  - AUUC
  - Uplift@K
- Experimentation utilities:
  - A/B simulation for random vs model targeting
  - incrementality metrics (ATE, incremental conversions, CPIC, ROI)
- Serving layer:
  - FastAPI app with `/v1/health` and `/v1/rank`
- Monitoring primitive:
  - PSI feature drift metric
- Unit tests for features, models, and serving health endpoint.

## Project layout

```text
src/
  data/
  features/
  models/
  experimentation/
  serving/
  monitoring/
tests/unit/
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
uvicorn serving.app:app --reload
```

## Notes

This implementation is intentionally lightweight and designed to be extensible toward:
- Optuna-based tuning
- MLflow model registry
- Redis/Parquet feature store
- dashboarding and advanced experiment statistics.
