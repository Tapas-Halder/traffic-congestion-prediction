from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import APP_NAME,FRONTEND_URL
from database import Base,engine
from routers.traffic import router
Base.metadata.create_all(bind=engine)
app=FastAPI(title=APP_NAME,version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"] if FRONTEND_URL=="*" else [x.strip() for x in FRONTEND_URL.split(",")],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.get("/")
def root(): return {"message":APP_NAME,"docs":"/docs"}
