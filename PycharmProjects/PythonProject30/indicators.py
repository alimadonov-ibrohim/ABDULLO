"""
Indikatorlar (SMA9/50, EMA200, RSI14, MACD, ADX14) va signal mantiqiy tekshiruvi.
"""
import pandas as pd


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]

    df["sma9"] = close.rolling(window=9).mean()
    df["sma50"] = close.rolling(window=50).mean()
    df["ema200"] = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = avg_loss.mask(avg_loss == 0, pd.NA)
    df["rsi"] = 100 - (100 / (1 + avg_gain / avg_loss))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    high = df["high"]
    low = df["low"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        [u if (u > d) and (u > 0) else 0.0 for u, d in zip(up_move, down_move)],
        index=df.index,
    )
    minus_dm = pd.Series(
        [d if (d > u) and (d > 0) else 0.0 for u, d in zip(up_move, down_move)],
        index=df.index,
    )
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    atr_safe = atr.mask(atr == 0, pd.NA)
    plus_di = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    minus_di = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr_safe
    di_sum = (plus_di + minus_di).mask(plus_di + minus_di == 0, pd.NA)
    dx = ((plus_di - minus_di).abs() / di_sum) * 100
    df["adx"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

    return df


def check_signal(df: pd.DataFrame) -> dict:
    """Oxirgi yopilgan sham bo'yicha BUY/SELL signali bor-yo'qligini tekshiradi."""
    result = {"signal": None, "details": {}}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    details = {
        "close": round(last["close"], 5),
        "sma9": round(last["sma9"], 5),
        "sma50": round(last["sma50"], 5),
        "ema200": round(last["ema200"], 5),
        "rsi": round(last["rsi"], 1),
        "macd": round(last["macd"], 5),
        "macd_signal": round(last["macd_signal"], 5),
        "adx": round(last["adx"], 1),
    }
    result["details"] = details

    if any(pd.isna(v) for k, v in details.items()):
        return result

    cross_up = prev["sma9"] <= prev["sma50"] and last["sma9"] > last["sma50"]
    cross_down = prev["sma9"] >= prev["sma50"] and last["sma9"] < last["sma50"]
    strong_trend = last["adx"] >= 20

    if strong_trend and cross_up and last["rsi"] < 70 and last["close"] > last["ema200"]:
        result["signal"] = "BUY"
    elif strong_trend and cross_down and last["rsi"] > 30 and last["close"] < last["ema200"]:
        result["signal"] = "SELL"

    if result["signal"]:
        entry = last["close"]
        sl_distance = max(entry * 0.003, abs(last["sma9"] - last["sma50"]))
        tp_distance = sl_distance * 2
        if result["signal"] == "SELL":
            stop_loss = entry + sl_distance
            take_profit = entry - tp_distance
        else:
            stop_loss = entry - sl_distance
            take_profit = entry + tp_distance
        details["stop_loss"] = round(stop_loss, 5)
        details["take_profit"] = round(take_profit, 5)
        details["risk_reward"] = 2

    return result
