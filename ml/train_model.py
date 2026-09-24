from pathlib import Path
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor
from sklearn.metrics import accuracy_score,f1_score,mean_absolute_error,r2_score
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parent
ARTIFACTS=ROOT/"artifacts"; ARTIFACTS.mkdir(exist_ok=True)
FEATURES=["speed","free_flow_speed","hour","day_of_week","is_weekend","lag_5","lag_15","lag_30","lag_60","rolling_mean_15","rolling_std_15","rolling_mean_60","temperature","rainfall","visibility","event_flag","congestion_index","speed_ratio","rain_heavy","weather_speed_penalty"]

def make_historical_data():
    rng=np.random.default_rng(42); rows=[]
    # Sensor-style baseline: 20 days x 8 routes at 5-minute resolution.
    for route_id in range(8):
        base_free=float(rng.uniform(42,68)); speeds=[]
        for i in range(20*288):
            hour=(i//12)%24; dow=(i//(12*24))%7; minute=(i%12)*5
            t=hour+minute/60
            morning=np.exp(-((t-8.5)/1.7)**2); evening=np.exp(-((t-18.5)/2.0)**2)
            # Rain has two effects: fewer vehicles can reduce demand, but heavy rain reduces safe speed.
            rain=max(0.0,float(rng.normal(1.2,0.9))) if rng.random()<0.22 else 0.0
            heavy_rain=1 if rain>=5 else 0
            event=1 if rng.random()<0.025 else 0
            demand_factor=0.36*morning+0.40*evening+0.10*event
            rain_penalty=min(0.32,0.018*rain+0.09*heavy_rain)
            rain_relief=min(0.08,0.012*rain)  # lower demand can partly offset congestion
            ratio=np.clip(0.98-demand_factor-rain_penalty+rain_relief,0.16,1.04)
            speed=float(np.clip(base_free*ratio+rng.normal(0,2.2),7,base_free*1.05))
            speeds.append(speed)
            if len(speeds)<13: continue
            def lag(minutes):
                return speeds[max(0,len(speeds)-1-minutes//5)]
            w15=np.asarray(speeds[-4:]); w60=np.asarray(speeds[-12:])
            temp=27+4*np.sin((t-14)*np.pi/12)+rng.normal(0,0.8)
            visibility=max(1000,10000-rain*1400-event*500+rng.normal(0,250))
            ratio=speed/base_free; congestion_index=1-ratio
            weather_penalty=min(1.0,0.018*rain+0.09*heavy_rain+max(0,5000-visibility)/25000)
            row=[speed,base_free,hour,dow,int(dow>=5),lag(5),lag(15),lag(30),lag(60),
                 float(w15.mean()),float(w15.std()),float(w60.mean()),temp,rain,visibility,event,
                 congestion_index,ratio,int(heavy_rain),weather_penalty]
            future_speed=speed if i+3>=len(speeds) else speeds[i+3]
            rows.append((row,future_speed))
    X=np.asarray([r[0] for r in rows],float); y_speed=np.asarray([r[1] for r in rows],float)
    future_ratio=y_speed/np.maximum(X[:,1],1)
    y_level=np.select([future_ratio>=.80,future_ratio>=.60,future_ratio>=.40],
                      ["Free Flow","Moderate","Heavy"],default="Severe")
    return X,y_speed,y_level

X,y_speed,y_level=make_historical_data()
X_train,X_test,y_speed_train,y_speed_test,y_level_train,y_level_test=train_test_split(
    X,y_speed,y_level,test_size=.2,random_state=42,stratify=y_level
)
regressor=RandomForestRegressor(n_estimators=60,max_depth=11,min_samples_leaf=3,
                                max_features="sqrt",random_state=42,n_jobs=-1)
classifier=RandomForestClassifier(n_estimators=60,max_depth=11,min_samples_leaf=3,
                                  max_features="sqrt",class_weight="balanced",
                                  random_state=42,n_jobs=-1)
regressor.fit(X_train,y_speed_train); classifier.fit(X_train,y_level_train)
pred_speed=regressor.predict(X_test); pred_level=classifier.predict(X_test)
metrics={"training_samples":int(len(X_train)),"test_samples":int(len(X_test)),
 "mae_kmh":round(float(mean_absolute_error(y_speed_test,pred_speed)),3),
 "r2":round(float(r2_score(y_speed_test,pred_speed)),3),
 "accuracy":round(float(accuracy_score(y_level_test,pred_level)),3),
 "f1_weighted":round(float(f1_score(y_level_test,pred_level,average="weighted")),3),
 "features":FEATURES,"target_horizon_minutes":15,
 "data_note":"Synthetic sensor-style baseline; replace with real Kolkata sensor history for production validation."}
joblib.dump({"regressor":regressor,"classifier":classifier,"features":FEATURES},
            ARTIFACTS/"traffic_models.joblib",compress=3)
(ARTIFACTS/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
print(json.dumps(metrics,indent=2))
