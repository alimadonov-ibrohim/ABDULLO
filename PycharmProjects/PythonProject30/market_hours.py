"""
Forex bozori dam olish kunlarini tekshirish moduli (UTC vaqtida).
Shanba butun kun, yakshanba Sidney sessiyasi ochilishiga qadar yopiq hisoblanadi.
"""
from datetime import datetime, timezone

MARKET_OPEN_HOUR_SUNDAY_UTC = 21


def is_weekend(now: datetime = None) -> bool:
    if now is None:
        now = datetime.now(timezone.utc)

    weekday = now.weekday()
    if weekday == 5:
        return True
    if weekday == 6 and now.hour < MARKET_OPEN_HOUR_SUNDAY_UTC:
        return True
    return False
