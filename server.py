from fastapi import FastAPI
import requests
from datetime import datetime
import pytz

app = FastAPI()

# ==============================
# 🔧 HELPER FUNCTIONS
# ==============================

def safe_get(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("❌ API Error:", e)
        return None


# 🌍 Get coordinates
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    res = safe_get(url)

    if not res or "results" not in res:
        return None

    data = res["results"][0]

    return {
        "city": data["name"],
        "country": data["country"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "timezone": data["timezone"]
    }


# 🌡 Weather
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    res = safe_get(url)

    if not res:
        return {}

    return res.get("current_weather", {})


# 🌫 AQI
def get_aqi(lat, lon):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5,us_aqi"
    res = safe_get(url)

    if not res:
        return {}

    return res.get("current", {})


# 🕒 Time (formatted)
def get_time(timezone):
    try:
        tz = pytz.timezone(timezone)
        dt = datetime.now(tz)
        return dt.strftime("%d %B %Y, %I:%M %p")
    except Exception as e:
        print("❌ Time error:", e)
        return "Timezone error"


# 🎉 Holiday
def get_today_holiday(country_code="IN"):
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        year = today[:4]

        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
        res = requests.get(url, timeout=10).json()

        for holiday in res:
            if holiday["date"] == today:
                return holiday["localName"]

        return "No major holiday today"
    except Exception as e:
        print("❌ Holiday error:", e)
        return "Unavailable"


# 📚 Fact
def get_today_fact():
    try:
        today = datetime.utcnow()
        url = f"http://numbersapi.com/{today.month}/{today.day}/date"
        return requests.get(url, timeout=10).text
    except Exception as e:
        print("❌ Fact error:", e)
        return "No fact available"


# ==============================
# 🧠 MCP TOOL HANDLER
# ==============================

@app.post("/tool")
def tool_handler(payload: dict):
    print("🔥 MCP SERVER HIT:", payload)

    tool = payload.get("tool")
    city = payload.get("input")

    # ==============================
    # ❤️ HEALTH CHECK
    # ==============================
    if tool == "healthCheck":
        return {
            "status": "ok",
            "server": "MCP running",
            "version": "V3"
        }

    # ==============================
    # VALIDATE CITY FOR CITY TOOLS
    # ==============================
    if tool != "healthCheck":
        coord = get_coordinates(city)
        if not coord:
            return {"error": "City not found"}

    # ==============================
    # 🌍 FULL CITY INFO
    # ==============================
    if tool == "getCityInfo":

        weather = get_weather(coord["latitude"], coord["longitude"])
        current_time = get_time(coord["timezone"])

        return {
            "source": "MCP_SERVER_V3",
            **coord,
            "weather": weather,
            "current_time": current_time
        }

    # ==============================
    # 🌡 WEATHER ONLY
    # ==============================
    elif tool == "getWeatherOnly":

        weather = get_weather(coord["latitude"], coord["longitude"])

        return {
            "source": "MCP_SERVER_V3",
            "city": coord["city"],
            "weather": weather
        }

    # ==============================
    # 🕒 TIME ONLY
    # ==============================
    elif tool == "getTimeOnly":

        current_time = get_time(coord["timezone"])

        return {
            "source": "MCP_SERVER_V3",
            "city": coord["city"],
            "current_time": current_time
        }

    # ==============================
    # 📍 COORDINATES ONLY
    # ==============================
    elif tool == "getCoordinatesOnly":

        return {
            "source": "MCP_SERVER_V3",
            **coord
        }

    # ==============================
    # 🌫 AQI ONLY
    # ==============================
    elif tool == "getAQI":

        aqi = get_aqi(coord["latitude"], coord["longitude"])

        return {
            "source": "MCP_SERVER_V3",
            "city": coord["city"],
            "aqi": aqi
        }

    # ==============================
    # 🎉 TODAY SPECIAL
    # ==============================
    elif tool == "getTodaySpecial":

        holiday = get_today_holiday("IN")
        fact = get_today_fact()

        return {
            "source": "MCP_SERVER_V3",
            "city": coord["city"],
            "today_special": {
                "holiday": holiday,
                "fact": fact
            }
        }

    # ==============================
    # 🔥 FULL INSIGHTS (BEST TOOL)
    # ==============================
    elif tool == "getFullInsights":

        weather = get_weather(coord["latitude"], coord["longitude"])
        current_time = get_time(coord["timezone"])
        aqi = get_aqi(coord["latitude"], coord["longitude"])
        holiday = get_today_holiday("IN")
        fact = get_today_fact()

        return {
            "source": "MCP_SERVER_V3",
            "city": coord["city"],
            "country": coord["country"],
            "latitude": coord["latitude"],
            "longitude": coord["longitude"],
            "weather": weather,
            "aqi": aqi,
            "current_time": current_time,
            "today_special": {
                "holiday": holiday,
                "fact": fact
            }
        }

    # ==============================
    # ❌ UNKNOWN TOOL
    # ==============================
    return {"error": f"Unknown tool: {tool}"}