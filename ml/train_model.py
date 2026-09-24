from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
OUT=Path(__file__).resolve().parent/"artifacts"; OUT.mkdir(exist_ok=True)
rng=np.random.default_rng(42); n=2500
speed=rng.uniform(5,80,n); free=rng.uniform(35,70,n); hour=rng.integers(0,24,n); weather=rng.uniform(0,100,n); ratio=speed/free
score=ratio-np.where((hour>=7)&(hour<=9),.12,0)-np.where((hour>=17)&(hour<=20),.14,0)-weather*.001
y=np.select([score>=.8,score>=.6,score>=.4],["Free Flow","Moderate","Heavy"],default="Severe")
X=np.column_stack([speed,free,hour,weather,ratio]); a,b,c,d=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
m=RandomForestClassifier(n_estimators=180,max_depth=12,random_state=42,class_weight="balanced"); m.fit(a,c)
print("accuracy:",accuracy_score(d,m.predict(b))); joblib.dump(m,OUT/"traffic_model.joblib")
