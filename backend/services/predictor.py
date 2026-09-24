from pathlib import Path
import json
import joblib
import numpy as np
from config import MODEL_PATH

LEVELS = ["Free Flow", "Moderate", "Heavy", "Severe"]

class Predictor:
    def __init__(self):
        model_path = Path(MODEL_PATH).parent / "traffic_models.joblib"
        self.bundle = joblib.load(model_path) if model_path.exists() else None
        metrics_path = Path(MODEL_PATH).parent / "metrics.json"
        self.metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

    def _features(self, speed, free_flow, hour, weather, history=None, day_of_week=0, event_flag=0):
        values = [float(x) for x in (history or [])[-12:]] + [float(speed)]

        def lag(minutes):
            return values[max(0, len(values) - 1 - minutes // 5)]

        w15 = np.asarray(values[-4:], dtype=float)
        w60 = np.asarray(values[-12:], dtype=float)
        rain = float(weather.get("rain_1h", 0) or 0)
        temperature = float(weather.get("temperature", 27) or 27)
        visibility = float(weather.get("visibility", 10000) or 10000)
        heavy_rain = int(rain >= 5)
        ratio = float(speed) / max(float(free_flow), 1)
        weather_penalty = min(
            1.0,
            0.018 * rain + 0.09 * heavy_rain + max(0, 5000 - visibility) / 25000
        )

        return np.array([[
            speed, free_flow, int(hour), int(day_of_week), int(day_of_week >= 5),
            lag(5), lag(15), lag(30), lag(60),
            float(w15.mean()), float(w15.std()), float(w60.mean()),
            temperature, rain, visibility, int(event_flag),
            1 - ratio, ratio, heavy_rain, weather_penalty
        ]], dtype=float)

    def _fallback(self, speed, free_flow, hour, weather, history=None):
        rain = float(weather.get("rain_1h", 0) or 0)
        visibility = float(weather.get("visibility", 10000) or 10000)
        ratio = speed / max(free_flow, 1)

        rush = 0.12 if hour in range(7, 10) else 0.14 if hour in range(17, 21) else 0
        # Rain has mixed effects: lower demand can help, while heavy rain slows vehicles.
        rain_penalty = min(
            0.22,
            0.018 * rain + 0.09 * int(rain >= 5) + max(0, 5000 - visibility) / 25000
        )
        score = ratio - rush - rain_penalty

        level = LEVELS[
            0 if score >= 0.80 else
            1 if score >= 0.60 else
            2 if score >= 0.40 else 3
        ]
        predicted = max(5, speed * (1 - rush * 0.25 - rain_penalty * 0.5))
        confidence = min(0.99, max(0.51, 0.55 + abs(score - 0.60)))
        return level, round(float(confidence), 3), round(float(predicted), 1)

    def predict_current(self, speed, free_flow, hour, weather, history=None, day_of_week=0):
        if not self.bundle:
            return self._fallback(speed, free_flow, hour, weather, history)

        x = self._features(speed, free_flow, hour, weather, history, day_of_week)
        classifier = self.bundle["classifier"]
        regressor = self.bundle["regressor"]

        level = str(classifier.predict(x)[0])
        probabilities = classifier.predict_proba(x)[0]
        predicted = float(regressor.predict(x)[0])

        return (
            level,
            round(float(max(probabilities)), 3),
            round(max(5, predicted), 1)
        )

    def forecast(self, speed, free_flow, hour, weather, history=None, day_of_week=0):
        values = list(history or [])[-12:]
        prediction = float(speed)
        out = []

        # Build the 15/30/45/60 minute forecast recursively.
        for step in range(1, 5):
            future_hour = (hour + (step * 15) // 60) % 24
            level, probability, prediction = self.predict_current(
                prediction, free_flow, future_hour, weather, values, day_of_week
            )
            values.append(prediction)
            out.append({
                "minutes_ahead": step * 15,
                "predicted_speed": round(float(prediction), 1),
                "congestion_level": level,
                "probability": probability,
            })

        return out

    def model_metrics(self):
        return self.metrics

predictor = Predictor()
