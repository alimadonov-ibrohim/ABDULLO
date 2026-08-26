"""Avto-signallarni real natija bo'yicha kuzatish.

Har bir ochiq signal (source='auto', status='open') signal berilgan
paytdan keyingi shamalar bo'yicha yuritiladi:
  • SL urilsa  -> status='lost'
  • TP1/TP2    -> tp_hits oshadi (signal kuzatishda qoladi)
  • TP3 urilsa -> status='won'

Bir shamada TP va SL birga tegsa — konservativ tarzda SL hisoblanadi.
"""

import asyncio
from datetime import datetime, timezone

import pandas as pd

import indicators_engine as ie
from database import db
from logger import get_logger

log = get_logger("signal_tracker")

_TRACK_LIMIT = 400
_track_lock = asyncio.Lock()


def _parse_created(value: str) -> pd.Timestamp | None:
    try:
        return pd.Timestamp(value)
    except (ValueError, TypeError):
        return None


def _walk_signal(row: dict, df: pd.DataFrame) -> tuple[str, int]:
    """(status, tp_hits) qaytaradi. status: open | won | lost"""
    direction = row["direction"]
    entry_ts = _parse_created(row["created_at"])

    if entry_ts is not None:
        sub = df[df["ts"] > entry_ts]
    else:
        sub = df

    if sub.empty:
        return "open", int(row["tp_hits"] or 0)

    sl = row["sl"]
    tps = [row["tp1"], row["tp2"], row["tp3"]]
    if sl is None or any(tp is None for tp in tps):
        return "open", int(row["tp_hits"] or 0)

    tp_hits = 0
    long = direction == "LONG"

    for _, candle in sub.iterrows():
        hit_sl = candle["low"] <= sl if long else candle["high"] >= sl
        if hit_sl:
            return "lost", tp_hits

        for i in range(tp_hits, 3):
            reached = (
                candle["high"] >= tps[i] if long else candle["low"] <= tps[i]
            )
            if reached:
                tp_hits = i + 1

        if tp_hits >= 3:
            return "won", tp_hits

    return "open", tp_hits


async def track_open_signals() -> int:
    """Ochiq avto-signallarni tekshirib, bazani yangilaydi.
    Yangilangan signal sonini qaytaradi."""
    async with _track_lock:
        rows = await db.open_auto_signals(limit=100)
        if not rows:
            return 0

        by_symbol: dict[str, list[dict]] = {}
        for r in rows:
            by_symbol.setdefault(r["symbol"], []).append(r)

        updated = 0
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        for symbol, group in by_symbol.items():
            meta = None
            try:
                from config import get_pair_meta, guess_pair_meta

                meta = get_pair_meta(symbol) or guess_pair_meta(symbol)
                screener = meta.get("screener", "crypto")
                if screener == "crypto":
                    df = await ie.fetch_binance_ohlc(symbol, "4h", limit=_TRACK_LIMIT)
                else:
                    df = await ie.fetch_twelvedata_ohlc(symbol, "4h", limit=_TRACK_LIMIT)
            except Exception:
                log.exception("klines fetch failed for %s", symbol)
                continue

            if df is None or "ts" not in df.columns:
                continue

            for row in group:
                try:
                    status, tp_hits = _walk_signal(row, df)
                    prev_hits = int(row["tp_hits"] or 0)

                    terminal = status in ("won", "lost")
                    changed = terminal or tp_hits != prev_hits
                    if not changed:
                        continue

                    new_status = (
                        status
                        if terminal
                        else ("running" if tp_hits > 0 else "open")
                    )
                    resolved = now_iso if terminal else None
                    await db.set_signal_progress(
                        row["id"], new_status, tp_hits, resolved_at=resolved
                    )
                    updated += 1
                    log.info(
                        "Signal #%s %s %s -> %s (TP%d)",
                        row["id"],
                        symbol,
                        row["direction"],
                        new_status,
                        tp_hits,
                    )
                except Exception:
                    log.exception("track failed for signal #%s", row["id"])

        return updated
