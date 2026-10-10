"""Smoke tests for the trained model artifact.

Run from repository root after training:
    python ml/test_model.py
"""
from predict import DEFAULT_MODEL_PATH, load_model


def main() -> None:
    bundle = load_model()
    assert "pipeline" in bundle
    assert "features" in bundle and bundle["features"]
    assert "target" in bundle
    print("PASS: trained model bundle loads.")
    print("Target:", bundle["target"])
    print("Features:", len(bundle["features"]))


if __name__ == "__main__":
    main()
