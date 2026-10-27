"""Load real observations without fabricating missing values."""
from pathlib import Path
import pandas as pd

def load_csv(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)
