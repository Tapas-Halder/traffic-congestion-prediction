from pathlib import Path
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parent
ARTIFACTS=ROOT/"artifacts"
ARTIFACTS.mkdir(exist_ok=True)

FEATURES=[
    "speed","free_flow_speed","hour","day_of_week","is_weekend",
    "lag_5","lag_15","lag_30","lag_60",
    "rolling_mean_15","rolling_std_15","rolling_mean_60",
    "temperature","rainfall","visibility","event_flag",
    "congestion_index","speed_ratio"
]

def make_historical_data():
    rng=np.random.default_rng(42)
    rows=[]
    # Synthetic historical sensor-like baseline used when a real sensor CSV is unavailable.
    # Each route has a repeatable daily pattern plus weather/event effects.
    for route_id in range(8):
        base_free=rng.uniform(42,68)
        speeds=[]
        for i in range(30*288):
            hour=(i//12)%24
            dow=(i//(12*24))%7
            minute=(i%12)*5
            rush_morning=np.exp(-((hour+minute/60-8.5)/1.7)**2)
            rush_evening=np.exp(-((hour+minute/60-18.5)/2.0)**2)
            rain=max(0.0,rng.normal(0.35,0.25)) if rng.random()<0.18 else 0.0
            event=1 if rng.random()<0.025 else 0
            weather_penalty=min(0.28,rain*0.08+event*0.10)
            ratio=max(0.18,0.98-0.36*rush_morning-0.40*rush_evening-weather_penalty)
            speed=float(np.clip(base_free*ratio+rng.normal(0,2.8),8,base_free*1.05))
            speeds.append(speed)
            if len(speeds)<13:
                continue
            def lag(minutes): return speeds[-1-min(minutes//5, len(speeds)-1)]
            last=speeds[-1]
            lag5=lag(5); lag15=lag(15); lag30=lag(30); lag60=lag(60)
            window15=np.array(speeds[-4:])
            window60=np.array(speeds[-12:])
            temp=27+4*np.sin((hour-14)*np.pi/12)+rng.normal(0,1)
            visibility=max(1500,10000-rain*3500-event*500+rng.normal(0,300))
            congestion_index=1-last/base_free
            row=[
                last,base_free,hour,dow,int(dow>=5),lag5,lag15,lag30,lag60,
                float(window15.mean()),float(window15.std()),float(window60.mean()),
                temp,rain,visibility,event,congestion_index,last/base_free
            ]
            # Target is 15 minutes ahead, matching the first required horizon.
            future_index=min(len(speeds)-1+3,90*288-1)
            future_speed=last
            if i+3 < 90*288:
                future_speed=speeds[i+3]
            rows.append((row,future_speed))
    X=np.asarray([r[0] for r in rows],dtype=float)
    y_speed=np.asarray([r[1] for r in rows],dtype=float)
    free=X[:,1]
    future_ratio=y_speed/np.maximum(free,1)
    y_level=np.select(
        [future_ratio>=0.80,future_ratio>=0.60,future_ratio>=0.40],
        ["Free Flow","Moderate","Heavy"],
        default="Severe",
    )
    return X,y_speed,y_level

X,y_speed,y_level=make_historical_data()
X_train,X_test,y_speed_train,y_speed_test=train_test_split(X,y_speed,test_size=.2,random_state=42)
_,_,y_level_train,y_level_test=train_test_split(X,y_level,test_size=.2,random_state=42)

regressor=RandomForestRegressor(
    n_estimators=140,max_depth=14,min_samples_leaf=2,random_state=42,n_jobs=-1
)
classifier=RandomForestClassifier(
    n_estimators=140,max_depth=14,min_samples_leaf=2,random_state=42,
    class_weight="balanced",n_jobs=-1
)
regressor.fit(X_train,y_speed_train)
classifier.fit(X_train,y_level_train)

pred_speed=regressor.predict(X_test)
pred_level=classifier.predict(X_test)
metrics={
    "training_samples":int(len(X_train)),
    "test_samples":int(len(X_test)),
    "mae_kmh":round(float(mean_absolute_error(y_speed_test,pred_speed)),3),
    "r2":round(float(r2_score(y_speed_test,pred_speed)),3),
    "accuracy":round(float(accuracy_score(y_level_test,pred_level)),3),
    "f1_weighted":round(float(f1_score(y_level_test,pred_level,average="weighted")),3),
    "features":FEATURES,
    "target_horizon_minutes":15,
    "data_note":"Synthetic sensor-style historical baseline; replace with real historical traffic data for production accuracy."
}
joblib.dump({"regressor":regressor,"classifier":classifier,"features":FEATURES},ARTIFACTS/"traffic_models.joblib")
(ARTIFACTS/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
print(json.dumps(metrics,indent=2))
