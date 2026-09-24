# Deploy Guide (বাংলা)

এই project-এ PostgreSQL/database রাখা হয়নি। Basic flow:

TomTom Traffic API + OpenWeather API
→ FastAPI backend
→ Random Forest ML
→ HTML/CSS/JS dashboard

## 1. API Key তৈরি

### TomTom Traffic API
1. TomTom Developer Portal-এ account তৈরি/login করুন।
2. API key তৈরি করুন।
3. Key কাউকে public chat/GitHub code-এ দেবেন না।
4. Render-এর Environment Variables-এ `TOMTOM_API_KEY` হিসেবে দিন।

### OpenWeather API
1. OpenWeather account তৈরি/login করুন।
2. Account-এর API Keys section থেকে key নিন।
3. Render-এ `OPENWEATHER_API_KEY` হিসেবে দিন।

## 2. Render Backend Deploy

Repository: `Tapas-Halder/traffic-congestion-prediction`

1. Render Dashboard খুলুন।
2. **New → Blueprint** নির্বাচন করুন।
3. GitHub repository connect করুন।
4. `render.yaml` select/confirm করুন।
5. Deploy শুরু করুন।
6. Initial setup-এ secret values চাইলে দিন:
   - `TOMTOM_API_KEY`
   - `OPENWEATHER_API_KEY`
   - `FRONTEND_URL=*`
7. Deploy শেষ হলে Render একটি URL দেবে, যেমন:
   `https://traffic-congestion-api.onrender.com`

### Backend test

Browser-এ খুলুন:

`https://YOUR-RENDER-URL.onrender.com/`

তারপর:

`https://YOUR-RENDER-URL.onrender.com/docs`

Health test:

`https://YOUR-RENDER-URL.onrender.com/api/health`

Expected:

`{"status":"ok"}`

## 3. Vercel Frontend Deploy

1. Vercel Dashboard খুলুন।
2. **Add New → Project**।
3. GitHub থেকে `traffic-congestion-prediction` import করুন।
4. **Root Directory = `frontend`** দিন।
5. Framework Preset = **Other** রাখুন।
6. Build command প্রয়োজন নেই।
7. Deploy করুন।

## 4. Frontend-কে Backend-এর সাথে Connect

Vercel deploy করার আগে বা পরে:

`frontend/app.js`

এই line খুঁজুন:

`const API_BASE="https://YOUR-RENDER-SERVICE.onrender.com";`

এখানে নিজের Render URL বসান।

উদাহরণ:

`const API_BASE="https://traffic-congestion-api.onrender.com";`

তারপর GitHub-এ commit/push করুন। Vercel connected থাকলে নতুন commit থেকে deployment হবে।

## 5. Render CORS

Frontend deploy হওয়ার পরে চাইলে Render-এর Environment Variables-এ:

`FRONTEND_URL=https://YOUR-VERCEL-DOMAIN.vercel.app`

দিতে পারেন।

Testing-এর সময় `FRONTEND_URL=*` রাখা যায়।

## 6. গুরুত্বপূর্ণ Security

- `.env` GitHub-এ upload করবেন না।
- API key HTML/JavaScript-এ রাখবেন না।
- API key শুধু backend/Render Environment Variables-এ রাখবেন।
- কোনো key public হয়ে গেলে সেটি revoke/rotate করে নতুন key ব্যবহার করুন।

## 7. Local Run

Terminal:

```bash
cd backend
pip install -r requirements.txt
cd ..
python ml/train_model.py
cd backend
uvicorn main:app --reload
```

Backend চলবে:

`http://127.0.0.1:8000`

Swagger:

`http://127.0.0.1:8000/docs`

## 8. Project Structure

```
traffic-congestion-prediction/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   ├── schemas/
│   └── services/
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── vercel.json
├── ml/
│   ├── train_model.py
│   └── artifacts/
├── render.yaml
└── README.md
```

## 9. 3 Member কাজ ভাগ

### Member 1 — Frontend
- `frontend/index.html`
- `frontend/style.css`
- `frontend/app.js`

### Member 2 — Backend + API
- `backend/main.py`
- `backend/routers/`
- `backend/services/tomtom.py`
- `backend/services/weather.py`
- API keys এবং Render deployment

### Member 3 — ML
- `ml/train_model.py`
- model training
- feature engineering
- prediction logic

## 10. Final Flow

User location
→ TomTom থেকে live traffic
→ OpenWeather থেকে weather
→ FastAPI feature তৈরি করে
→ Random Forest congestion predict করে
→ Frontend dashboard-এ result দেখায়
