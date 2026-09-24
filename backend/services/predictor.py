from pathlib import Path
import json
import joblib
import numpy as np
from config import MODEL_PATH

LEVELS=["Free Flow","Moderate","Heavy","Severe"]
FEATURES=[
    "speed","free_flow_speed","hour","day_of_week","is_weekend",
    "lag_5","lag_15","lag_30","lag_60",
    "rolling_mean_15","rolling_std_15","rolling_mean_60",
    "temperature","rainfall","visibility","event_flag",
    "congestion_index","speed_ratio"
]

class Predictor:
    def __init__(self):
        model_path=Path(MODEL_PATH).parent/"traffic_models.joblib"
        self.bundle=joblib.load(model_path) if model_path.exists() else None
        metrics_path=Path(MODEL_PATH).parent/"metrics.json"
        self.metrics=json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

    def _features(self,speed,free_flow,hour,weather,history=None,day_of_week=0,event_flag=0):
        history=list(history or [])
        series=[float(x) for x in history[-12:]]+[float(speed)]
        def lag(minutes):
            idx=max(0,len(series)-1-(minutes//5))
            return series[idx]
        last=series[-1]
        w15=np.asarray(series[-4:],dtype=float)
        w60=np.asarray(series[-12:],dtype=float)
        rainfall=float(weather.get("rain_1h",0) or 0)
        temp=float(weather.get("temperature",27) or 27)
        visibility=float(weather.get("visibility",10000) or 10000)
        ratio=last/max(float(free_flow),1)
        return np.array([[
            last,float(free_flow),int(hour),int(day_of_week),int(day_of_week>=5),
            lag(5),lag(15),lag(30),lag(60),
            float(w15.mean()),float(w15.std()),float(w60.mean()),
            temp,rainfall,visibility,int(event_flag),
            1-ratio,ratio
        ]],dtype=float)

    def _fallback(self,speed,free_flow,hour,weather):
        ratio=speed/max(free_flow,1)
        rush=0.12 if hour in range(7,10) else 0.14 if hour in range(17,21) else 0
        weather_penalty=min(.15,float(weather.get("weather_impact",0))/700)
        score=ratio-rush-weather_penalty
        level=LEVELS[0 if score>=.8 else 1 if score>=.6 else 2 if score>=.4 else 3]
        probability=min(.99,max(.51,1-score if level!="Free Flow" else score))
        predicted=max(5,speed*(1-rush*.25-weather_penalty*.5))
        return level,round(float(probability),3),round(float(predicted),1)

    def predict_current(self,speed,free_flow,hour,weather,history=None,day_of_week=0):
        if not self.bundle:
            return self._fallback(speed,free_flow,hour,weather)
        x=self._features(speed,free_flow,hour,weather,history,day_of_week)
        classifier=self.bundle["classifier"]
        regressor=self.bundle["regressor"]
        level=str(classifier.predict(x)[0])
        probs=classifier.predict_proba(x)[0]
        probability=float(max(probs))
        predicted=float(regressor.predict(x)[0])
        return level,round(probability,3),round(max(5,predicted),1)

    def forecast(self,speed,free_flow,hour,weather,history=None,day_of_week=0):
        values=list(history or [])[-12:]
        current=float(speed)
        out=[]
        for horizon in (15,30,45,60):
            steps=(horizon//15)
            pred=current
            for _ in range(steps if not out else 1):
                future_hour=(hour+((len(out)+1)*15)//60)%24
                level,prob,pred=self.predict_current(
                    pred,free_flow,future_hour,weather,values,day_of_week
                )
                values.append(pred)
            out.append({
                "minutes_ahead":horizon,
                "predicted_speed":round(float(pred),1),
                "congestion_level":level,
                "probability":prob
            })
        return out

    def model_metrics(self):
        return self.metrics

predictor=Predictor()
