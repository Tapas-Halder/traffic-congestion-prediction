from pathlib import Path
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

FEATURES = [
    "speed", "free_flow_speed", "hour", "day_of_week", "is_weekend",
    "lag_5", "lag_15", "lag_30", "lag_60", "rolling_mean_15",
    "rolling_std_15", "rolling_mean_60", "temperature", "rainfall",
    "visibility", "event_flag", "congestion_index", "speed_ratio",
    "rain_heavy", "weather_speed_penalty"
]

def make_historical_data():
    rng = np.random.default_rng(42)
    rows = []

    for route_id in range(8):
        base_free = float(rng.uniform(42, 68))
        total = 20 * 288
        speeds, rains, temperatures, visibilities = [], [], [], []
        events, hours, dows = [], [], []

        for i in range(total):
            hour = (i // 12) % 24
            dow = (i // (12 * 24)) % 7
            minute = (i % 12) * 5
            t = hour + minute / 60

            morning = np.exp(-((t - 8.5) / 1.7) ** 2)
            evening = np.exp(-((t - 18.5) / 2.0) ** 2)
            rain = max(0.0, float(rng.normal(1.2, 0.9))) if rng.random() < 0.22 else 0.0
            heavy_rain = int(rain >= 5)
            event = int(rng.random() < 0.025)

            demand_factor = 0.36 * morning + 0.40 * evening + 0.10 * event
            rain_penalty = min(0.32, 0.018 * rain + 0.09 * heavy_rain)
            rain_relief = min(0.08, 0.012 * rain)
            ratio = np.clip(0.98 - demand_factor - rain_penalty + rain_relief, 0.16, 1.04)

            speed = float(np.clip(base_free * ratio + rng.normal(0, 2.2), 7, base_free * 1.05))
            temperature = 27 + 4 * np.sin((t - 14) * np.pi / 12) + rng.normal(0, 0.8)
            visibility = max(1000, 10000 - rain * 1400 - event * 500 + rng.normal(0, 250))

            speeds.append(speed)
            rains.append(rain)
            temperatures.append(temperature)
            visibilities.append(visibility)
            events.append(event)
            hours.append(hour)
            dows.append(dow)

        for i in range(12, total - 3):
            speed = speeds[i]
            free = base_free
            history = speeds[:i + 1]

            def lag(minutes):
                return history[max(0, len(history) - 1 - minutes // 5)]

            w15 = np.asarray(history[-4:], dtype=float)
            w60 = np.asarray(history[-12:], dtype=float)
            rain = float(rains[i])
            heavy_rain = int(rain >= 5)
            visibility = float(visibilities[i])
            ratio = speed / max(free, 1)
            weather_penalty = min(
                1.0,
                0.018 * rain + 0.09 * heavy_rain + max(0, 5000 - visibility) / 25000
            )

            row = [
                speed, free, hours[i], dows[i], int(dows[i] >= 5),
                lag(5), lag(15), lag(30), lag(60),
                float(w15.mean()), float(w15.std()), float(w60.mean()),
                float(temperatures[i]), rain, visibility, events[i],
                1 - ratio, ratio, heavy_rain, weather_penalty
            ]
            rows.append((row, float(speeds[i + 3])))

    X = np.asarray([r[0] for r in rows], dtype=float)
    y_speed = np.asarray([r[1] for r in rows], dtype=float)
    future_ratio = y_speed / np.maximum(X[:, 1], 1)
    y_level = np.select(
        [future_ratio >= 0.80, future_ratio >= 0.60, future_ratio >= 0.40],
        ["Free Flow", "Moderate", "Heavy"],
        default="Severe"
    )
    return X, y_speed, y_level

X, y_speed, y_level = make_historical_data()

# A rare synthetic class can contain only one sample. In that case
# stratified splitting is impossible, so use a normal random split.
unique, counts = np.unique(y_level, return_counts=True)
can_stratify = len(unique) > 1 and counts.min() >= 2
stratify_target = y_level if can_stratify else None

X_train, X_test, y_speed_train, y_speed_test, y_level_train, y_level_test = train_test_split(
    X, y_speed, y_level, test_size=0.2, random_state=42, stratify=stratify_target
)

regressor = RandomForestRegressor(
    n_estimators=60, max_depth=11, min_samples_leaf=3,
    max_features="sqrt", random_state=42, n_jobs=-1
)
classifier = RandomForestClassifier(
    n_estimators=60, max_depth=11, min_samples_leaf=3,
    max_features="sqrt", class_weight="balanced",
    random_state=42, n_jobs=-1
)

regressor.fit(X_train, y_speed_train)
classifier.fit(X_train, y_level_train)

pred_speed = regressor.predict(X_test)
pred_level = classifier.predict(X_test)

metrics = {
    "training_samples": int(len(X_train)),
    "test_samples": int(len(X_test)),
    "mae_kmh": round(float(mean_absolute_error(y_speed_test, pred_speed)), 3),
    "r2": round(float(r2_score(y_speed_test, pred_speed)), 3),
    "accuracy": round(float(accuracy_score(y_level_test, pred_level)), 3),
    "f1_weighted": round(float(f1_score(y_level_test, pred_level, average="weighted")), 3),
    "features": FEATURES,
    "target_horizon_minutes": 15,
    "data_note": "Synthetic sensor-style baseline; replace with real Kolkata historical traffic data for real-world validation.",
    "stratified_split": bool(can_stratify)
}

joblib.dump(
    {"regressor": regressor, "classifier": classifier, "features": FEATURES},
    ARTIFACTS / "traffic_models.joblib",
    compress=3
)
(ARTIFACTS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
print(json.dumps(metrics, indent=2))
