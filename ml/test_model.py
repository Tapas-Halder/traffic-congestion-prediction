from pathlib import Path
import joblib

MODEL_PATH = Path(
    "ml/artifacts/congestion_model.joblib"
)


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Run python ml/train_model.py first."
        )

    bundle = joblib.load(MODEL_PATH)

    assert "pipeline" in bundle
    assert "features" in bundle

    print("PASS: model loaded successfully.")
    print("Features:", bundle["features"])
    print("Classes:", list(bundle["pipeline"].classes_))


if __name__ == "__main__":
    main()