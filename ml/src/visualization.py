"""Save a simple real-data speed chart for the project report."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ml.src.data_loader import load_csv

def save_speed_plot(csv_path, output_path):
    df = load_csv(csv_path)
    if "current_speed_kmph" not in df:
        raise ValueError("current_speed_kmph column missing")
    speed = __import__("pandas").to_numeric(df["current_speed_kmph"], errors="coerce").dropna()
    if speed.empty:
        raise ValueError("No real speed observations to plot")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(speed, bins=30)
    ax.set(xlabel="Current speed (km/h)", ylabel="Observations", title="Kolkata traffic speed distribution")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
