from pathlib import Path
import json,joblib,numpy as np
from config import MODEL_PATH
LEVELS=["Free Flow","Moderate","Heavy","Severe"]
FEATURES=["speed","free_flow_speed","hour","day_of_week","is_weekend","lag_5","lag_15","lag_30","lag_60","rolling_mean_15","rolling_std_15","rolling_mean_60","temperature","rainfall","visibility","event_flag","congestion_index","speed_ratio","rain_heavy","weather_speed_penalty"]

class Predictor:
 def __init__(self):
  model_path=Path(MODEL_PATH).parent/"traffic_models.joblib"
  self.bundle=joblib.load(model_path) if model_path.exists() else None
  metrics_path=Path(MODEL_PATH).parent/"metrics.json"
  self.metrics=json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
 def _features(self,speed,free_flow,hour,weather,history=None,day_of_week=0,event_flag=0):
  values=[float(x) for x in (history or [])[-12:]]+[float(speed)]
  def lag(minutes): return values[max(0,len(values)-1-minutes//5)]
  w15=np.asarray(values[-4:],float); w60=np.asarray(values[-12:],float)
  rain=float(weather.get("rain_1h",0) or 0); temp=float(weather.get("temperature",27) or 27)
  visibility=float(weather.get("visibility",10000) or 10000); heavy=int(rain>=5)
  ratio=float(speed)/max(float(free_flow),1)
  penalty=min(1.0,.018*rain+.09*heavy+max(0,5000-visibility)/25000)
  return np.array([[speed,free_flow,int(hour),int(day_of_week),int(day_of_week>=5),
   lag(5),lag(15),lag(30),lag(60),float(w15.mean()),float(w15.std()),float(w60.mean()),
   temp,rain,visibility,int(event_flag),1-ratio,ratio,heavy,penalty]],float)
 def _fallback(self,speed,free_flow,hour,weather,history=None):
  rain=float(weather.get("rain_1h",0) or 0); visibility=float(weather.get("visibility",10000) or 10000)
  ratio=speed/max(free_flow,1); rush=.12 if hour in range(7,10) else .14 if hour in range(17,21) else 0
  # Heavy rain may lower demand, but its road-safety effect lowers speed and raises delay risk.
  rain_effect=min(.22,.018*rain+.09*int(rain>=5)+max(0,5000-visibility)/25000)
  score=ratio-rush-rain_effect
  level=LEVELS[0 if score>=.8 else 1 if score>=.6 else 2 if score>=.4 else 3]
  predicted=max(5,speed*(1-rush*.25-rain_effect*.5))
  return level,round(float(min(.99,max(.51,.55+abs(score-.6)))),3),round(float(predicted),1)
 def predict_current(self,speed,free_flow,hour,weather,history=None,day_of_week=0):
  if not self.bundle:return self._fallback(speed,free_flow,hour,weather,history)
  x=self._features(speed,free_flow,hour,weather,history,day_of_week)
  c=self.bundle["classifier"]; r=self.bundle["regressor"]
  level=str(c.predict(x)[0]); p=c.predict_proba(x)[0]; pred=float(r.predict(x)[0])
  return level,round(float(max(p)),3),round(max(5,pred),1)
 def forecast(self,speed,free_flow,hour,weather,history=None,day_of_week=0):
  values=list(history or [])[-12:]; current=float(speed); out=[]
  for horizon in (15,30,45,60):
   steps=horizon//15; pred=current; level="Free Flow"; prob=.5
   for _ in range(steps):
    future_hour=(hour+(len(out)+1)*15//60)%24
    level,prob,pred=self.predict_current(pred,free_flow,future_hour,weather,values,day_of_week)
    values.append(pred)
   out.append({"minutes_ahead":horizon,"predicted_speed":round(float(pred),1),
               "congestion_level":level,"probability":prob})
  return out
 def model_metrics(self): return self.metrics
predictor=Predictor()
