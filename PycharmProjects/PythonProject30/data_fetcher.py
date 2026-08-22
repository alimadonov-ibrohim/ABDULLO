"""
Twelve Data API orqali sham chaqirtiqlarini yuklab olish moduli.
"""
import requests
import pandas as pd


class DataFetcher:
    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_candles(self, symbol: str, interval: str = "15min", outputsize: int = 210) -> pd.DataFrame:
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key,
            "format": "JSON",
        }
        response = requests.get(self.BASE_URL, params=params, timeout=15)
        data = response.json()

        if data.get("status") == "error" or "values" not in data:
            raise RuntimeError(data.get("message", "Twelve Data javobi noto'g'ri"))

        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "datetime"})
        df["datetime"] = pd.to_datetime(df["datetime"])
        for col in ("open", "high", "low", "close"):
            df[col] = pd.to_numeric(df[col])
        if "volume" in df.columns:
            df["volume"] = pd.to_numeric(df["volume"])

        df = df.sort_values("datetime").reset_index(drop=True)
        return df
