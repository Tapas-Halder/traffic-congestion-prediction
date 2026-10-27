"""ML entry point: python -m ml.main [clean|train|all|test|analyze]."""
import argparse
from ml.config import RAW_CSV, PROCESSED_CSV, MODEL_PATH
from ml.clean_data import clean_csv
from ml.train_model import train

def main():
    parser = argparse.ArgumentParser(description="Kolkata TrafficIQ Random Forest ML pipeline")
    parser.add_argument("action", choices=["clean", "train", "all", "test", "analyze"], nargs="?", default="all")
    args = parser.parse_args()
    if args.action in ("clean", "all"):
        clean_csv(RAW_CSV, PROCESSED_CSV)
    if args.action in ("train", "all"):
        train(PROCESSED_CSV, MODEL_PATH)
    if args.action == "test":
        from ml.test_model import main as run_tests
        run_tests()
    if args.action == "analyze":
        from ml.src.analysis import summarize_data
        print(summarize_data(RAW_CSV))

if __name__ == "__main__":
    main()
