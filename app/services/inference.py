from __future__ import annotations
import os
import joblib
import numpy as np
from typing import Tuple

from app.config import get_settings


class FraudModel:
    _instance: "FraudModel" | None = None

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = joblib.load(model_path)
        self.settings = get_settings()

    @classmethod
    def instance(cls) -> "FraudModel":
        if cls._instance is None:
            settings = get_settings()
            cls._instance = FraudModel(settings.MODEL_PATH)
        return cls._instance

    def score(self, features: np.ndarray) -> float:
        # scikit IsolationForest: decision_function, higher -> more normal
        s = float(self.model.decision_function(features)[0])
        return s

    def predict_from_transaction(self, payload: dict) -> Tuple[float, bool]:
        # Minimal featureization: amount only for demo
        amt = float(payload.get("amount", 0.0))
        x = np.array([[amt]], dtype=float)
        score = self.score(x)
        is_fraud = score < self.settings.IFOREST_THRESHOLD
        return score, is_fraud
