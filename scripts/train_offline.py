import os
import pathlib
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest


def main():
    # Synthetic data: normal amounts ~ N(50, 10), outliers ~ N(200, 50)
    rng = np.random.default_rng(42)
    normal = rng.normal(50, 10, size=1000)
    outliers = rng.normal(200, 50, size=50)
    X = np.concatenate([normal, outliers]).reshape(-1, 1).astype(float)

    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X)

    model_path = os.environ.get("MODEL_PATH", "./app/models/artifacts/iforest.pkl")
    pathlib.Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
