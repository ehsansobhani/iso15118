import pandas as pd

from models.s_learner import SLearner


def test_s_learner_predicts_uplift() -> None:
    x = pd.DataFrame({"age": [20, 30, 40, 50], "gender": ["M", "F", "F", "M"]})
    treatment = pd.Series([1, 0, 1, 0])
    target = pd.Series([1, 0, 1, 0])

    model = SLearner().fit(x, treatment, target)
    pred = model.predict_uplift(x)
    assert len(pred) == 4
