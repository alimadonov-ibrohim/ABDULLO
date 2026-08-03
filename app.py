import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

RAINVIEWER_URL = "https://api.rainviewer.com/public/weather-maps.json"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/radar")
def radar():
    try:
        resp = requests.get(RAINVIEWER_URL, timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/weather")
def weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat va lon parametrlari kerak"}), 400
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 5,
        "timezone": "auto",
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "q parametri kerak"}), 400
    params = {"name": q, "count": 8, "language": "uz", "format": "json"}
    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return jsonify([
            {"name": r["name"], "country": r.get("country", ""),
             "lat": r["latitude"], "lon": r["longitude"]}
            for r in results
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(debug=True)
