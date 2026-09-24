import os

from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

TRAFFIC_API_URL = os.getenv("NB0SZBoWrJNALAGVMgK7ESo09TGNFvdV")

TRAFFIC_API_KEY = os.getenv("TRAFFIC_API_KEY")
