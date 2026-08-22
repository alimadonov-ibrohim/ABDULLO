from datetime import datetime, timezone

WEEKEND_WEEKDAYS = {5, 6}  # Shanba=5, Yakshanba=6 (Python weekday(), UTC)


def is_weekend_utc(dt: datetime | None = None) -> bool:
    """Bozor shanba/yakshanba kunlari yopiq (UTC)."""
    dt = dt or datetime.now(timezone.utc)
    return dt.weekday() in WEEKEND_WEEKDAYS


def next_open_day_label(lang: str) -> str:
    from utils.i18n import t

    return t(lang, "market_closed")
