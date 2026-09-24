from pathlib import Path
import joblib,numpy as np
from config import MODEL_PATH
LEVELS=["Free Flow","Moderate","Heavy","Severe"]
class Predictor:
 def __init__(self): self.model=joblib.load(MODEL_PATH) if Path(MODEL_PATH).exists() else None
 def predict(self,speed,free_flow,hour,weather):
  ratio=speed/max(free_flow,1)
  if self.model is None:
   label=LEVELS[0 if ratio>=.8 else 1 if ratio>=.6 else 2 if ratio>=.4 else 3]; return label,round(min(.99,max(.51,1-ratio)),3),round(max(0,speed*(1-.08*weather/100)),2)
  x=np.array([[speed,free_flow,hour,weather,ratio]]); p=self.model.predict_proba(x)[0]
  return str(self.model.predict(x)[0]),round(float(max(p)),3),round(float(speed*(.96 if hour in range(7,10) or hour in range(17,21) else 1.02)),2)
predictor=Predictor()
