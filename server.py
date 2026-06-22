from fastapi import FastAPI
import requests
from datetime import datetime
import pytz

app = FastAPI()

# ==============================
# 🔧 SAFE REQUEST HELPERS
# ==============================

def safe_get_json(url):
    try:
        res = requests.get(url, timeout=8)

        if res.status_code != 200:
            print("❌ Bad status:", res.status_code)
            return None

        if not res.text.strip():
            print("❌ Empty response")
            return None

        return res.json()

    except Exception as e:
        print("❌ JSON API Error:", e)
        return None


def safe_get_text(url):
    try:
        res = requests.get(url, timeout=8)

        if res.status_code != 200:
            print("❌ Text API status:", res.status_code)
            return None

        return res.text

    except Exception as e:
        print("❌ TEXT API Error:", e)
        return None


# ==============================
# 🌍 COORDINATES
# ==============================

def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    res = safe_get_json(url)

    if not res or "results" not in res or not res["results"]:
        return None

    data = res["results"][0]

    return {
        "city": data.get("name"),
        "country": data.get("country"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone")
    }


# ==============================
# 🌡 WEATHER
# ==============================

def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    res = safe_get_json(url)

    if not res:
        return None

    return res.get("current_weather")


# ==============================
# 🌫 AQI
# ==============================

def get_aqi(lat, lon):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5,us_aqi"
    res = safe_get_json(url)

    if not res:
        return None

    return res.get("current")


# ==============================
# 🕒 TIME
# ==============================

def get_time(timezone):
    try:
        tz = pytz.timezone(timezone)
        dt = datetime.now(tz)
        return dt.strftime("%d %B %Y, %I:%M %p")
    except Exception as e:
        print("❌ Time error:", e)
        return None


# ==============================
# 🎉 HOLIDAY
# ==============================

def get_today_holiday(country_code="IN"):
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        year = today[:4]

        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
        res = safe_get_json(url)

        if not res:
            return None

        for holiday in res:
            if holiday.get("date") == today:
                return holiday.get("localName")

        return None

    except Exception as e:
        print("❌ Holiday error:", e)
        return None


# ==============================
# 📚 FACT (FIXED)
# ==============================

def get_today_fact():
    try:
        today = datetime.utcnow()
        url = f"http://numbersapi.com/{today.month}/{today.day}/date"

        res = requests.get(url, timeout=8)

        if res.status_code != 200:
            return None

        return res.text

    except Exception as e:
        print("❌ Fact error:", e)
        return None


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
            "version": "V5-FINAL"
        }

    # ==============================
    # 🚫 VALIDATION
    # ==============================

    if not city:
        return {"error": "No city provided"}

    coord = get_coordinates(city)

    if not coord:
        return {"error": "City not found"}

    lat = coord["latitude"]
    lon = coord["longitude"]

    # ==============================
    # 🔥 FULL INSIGHTS (MAIN TOOL)
    # ==============================

    if tool == "getFullInsights":

        result = {
            "source": "MCP_SERVER_V5",
            "city": coord["city"],
            "country": coord["country"],
            "latitude": lat,
            "longitude": lon
        }

        # 🌡 Weather
        weather = get_weather(lat, lon)
        if weather:
            result["weather"] = weather

        # 🌫 AQI
        aqi = get_aqi(lat, lon)
        if aqi:
            result["aqi"] = aqi

        # 🕒 Time
        current_time = get_time(coord["timezone"])
        if current_time:
            result["current_time"] = current_time

        # 🎉 Special
        special = {}

        holiday = get_today_holiday("IN")
        if holiday:
            special["holiday"] = holiday

        fact = get_today_fact()
        if fact:
            special["fact"] = fact

        if special:
            result["today_special"] = special

        return result

    # ==============================
    # ❌ UNKNOWN TOOL
    # ==============================

    return {"error": f"Unknown tool: {tool}"}