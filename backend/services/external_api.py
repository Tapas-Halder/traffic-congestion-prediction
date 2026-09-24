import requests

from config import TRAFFIC_API_URL, TRAFFIC_API_KEY


def get_external_traffic_data(location: str):

    params = {
        "location": location,
        "api_key": TRAFFIC_API_KEY
    }

    response = requests.get(
        TRAFFIC_API_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()
