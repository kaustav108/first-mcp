from fastapi import FastAPI
import requests

app = FastAPI()

# ✅ 1. Get coordinates from city name
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    res = requests.get(url).json()

    if "results" not in res:
        return None

    data = res["results"][0]

    return {
        "city": data["name"],
        "country": data["country"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "timezone": data["timezone"]
    }

# ✅ 2. Get weather data
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    res = requests.get(url).json()

    return res.get("current_weather", {})

# ✅ 3. Get current time
from datetime import datetime
import pytz

def get_time(timezone):
    try:
        tz = pytz.timezone(timezone)
        return datetime.now(tz).isoformat()
    except:
        return "Timezone error"

# ✅ MCP Tool Endpoint
@app.post("/tool")
def tool_handler(payload: dict):
    tool = payload.get("tool")
    city = payload.get("input")

    if tool == "getCityInfo":

        coord = get_coordinates(city)

        if not coord:
            return {"error": "City not found"}

        weather = get_weather(coord["latitude"], coord["longitude"])
        current_time = get_time(coord["timezone"])

        return {
            "city": coord["city"],
            "country": coord["country"],
            "latitude": coord["latitude"],
            "longitude": coord["longitude"],
            "timezone": coord["timezone"],
            "weather": weather,
            "current_time": current_time
        }

    return {"error": "Unknown tool"}