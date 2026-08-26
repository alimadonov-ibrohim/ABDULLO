"""Price Action moduli: Liquidity Swings (LuxAlgo uslubi) va
Market Structure / BOS / CHoCH (Price Action Suite uslubi).

TradingView'dagi maxsus Pine Script indikatorlar API orqali berilmaydi,
shu sababli ularning mantiqi mahalliy OHLC ma'lumotlarida qayta yozildi.
"""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class LiquidityPool:
    price: float
    kind: str  # "BSL" (yuqorida, buy-side) | "SSL" (pastda, sell-side)
    touches: int


@dataclass
class LiquidityReport:
    pools_above: list[LiquidityPool] = field(default_factory=list)
    pools_below: list[LiquidityPool] = field(default_factory=list)
    swept_bullish: bool = False  # pastki likvidlik surib tashlangan (stop-hunt) -> bullish
    swept_bearish: bool = False  # yuqori likvidlik surilgan -> bearish


@dataclass
class StructureReport:
    trend: str = "NEUTRAL"  # BULLISH | BEARISH | NEUTRAL
    event: str | None = None  # BOS | CHOCH_BULL | CHOCH_BEAR
    event_level: float | None = None


@dataclass
class PriceActionReport:
    structure: StructureReport = field(default_factory=StructureReport)
    liquidity: LiquidityReport = field(default_factory=LiquidityReport)


def _pivots(highs, lows, order: int):
    n = len(highs)
    ph, pl = [], []
    for i in range(order, n - order):
        seg_h = highs[i - order : i + order + 1]
        seg_l = lows[i - order : i + order + 1]
        if highs[i] >= seg_h.max():
            ph.append(i)
        if lows[i] <= seg_l.min():
            pl.append(i)
    return ph, pl


def _cluster(levels: list[float], tol: float) -> list[tuple[float, int]]:
    """Yaqin darajalarni guruhlaydi; (o'rtacha, tegishlar_soni) qaytaradi."""
    if not levels:
        return []
    levels_sorted = sorted(levels)
    groups: list[list[float]] = [[levels_sorted[0]]]
    base = levels_sorted[0]
    for lv in levels_sorted[1:]:
        if abs(lv - base) / max(base, 1e-12) <= tol:
            groups[-1].append(lv)
            base = sum(groups[-1]) / len(groups[-1])
        else:
            groups.append([lv])
            base = lv
    return [(round(sum(g) / len(g), 8), len(g)) for g in groups]


def _swings(highs, lows, order: int):
    """Xronologik navbatlashgan H/L swing nuqtalari."""
    ph, pl = _pivots(highs, lows, order)
    raw = [(i, "H", float(highs[i])) for i in ph] + [(i, "L", float(lows[i])) for i in pl]
    raw.sort(key=lambda x: x[0])

    seq: list[list] = []
    for idx, typ, px in raw:
        if seq and seq[-1][1] == typ:
            if (typ == "H" and px > seq[-1][2]) or (typ == "L" and px < seq[-1][2]):
                seq[-1] = [idx, typ, px]
        else:
            seq.append([idx, typ, px])
    return seq


def scan_liquidity(
    df: pd.DataFrame,
    order: int = 5,
    tol: float = 0.002,
    max_pools: int = 3,
    sweep_lookback: int = 4,
) -> LiquidityReport:
    rep = LiquidityReport()
    if df is None or len(df) < (order * 2 + 8):
        return rep

    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    closes = df["close"].to_numpy(dtype=float)
    price = closes[-1]

    ph, pl = _pivots(highs, lows, order)

    recent_h = [float(highs[i]) for i in ph[-14:]]
    recent_l = [float(lows[i]) for i in pl[-14:]]

    for lvl, touches in _cluster(recent_h, tol):
        if touches >= 2 and lvl > price:
            rep.pools_above.append(LiquidityPool(lvl, "BSL", touches))
    for lvl, touches in _cluster(recent_l, tol):
        if touches >= 2 and lvl < price:
            rep.pools_below.append(LiquidityPool(lvl, "SSL", touches))

    rep.pools_above.sort(key=lambda p: p.price)
    del rep.pools_above[max_pools:]
    rep.pools_below.sort(key=lambda p: p.price, reverse=True)
    del rep.pools_below[max_pools:]

    tail = slice(max(0, len(df) - sweep_lookback), len(df))
    tail_low = lows[tail]
    tail_high = highs[tail]
    tail_close = closes[tail]

    if rep.pools_below:
        nearest_ssl = rep.pools_below[0].price
        for lo, cl in zip(tail_low, tail_close):
            if lo < nearest_ssl and cl > nearest_ssl:
                rep.swept_bullish = True
                break

    if rep.pools_above:
        nearest_bsl = rep.pools_above[-1].price
        for hi, cl in zip(tail_high, tail_close):
            if hi > nearest_bsl and cl < nearest_bsl:
                rep.swept_bearish = True
                break

    return rep


def scan_structure(df: pd.DataFrame, order: int = 5, confirm_recent: int = 3) -> StructureReport:
    rep = StructureReport()
    if df is None or len(df) < (order * 2 + 8):
        return rep

    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    closes = df["close"].to_numpy(dtype=float)
    n = len(closes)

    seq = _swings(highs, lows, order)
    swing_h = [s for s in seq if s[1] == "H"]
    swing_l = [s for s in seq if s[1] == "L"]
    if len(swing_h) < 2 or len(swing_l) < 2:
        return rep

    hh = swing_h[-1][2] > swing_h[-2][2]
    hl = swing_l[-1][2] > swing_l[-2][2]
    if hh and hl:
        trend = "BULLISH"
    elif (not hh) and (not hl):
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"

    last_h_idx, _, last_h_px = swing_h[-1]
    last_l_idx, _, last_l_px = swing_l[-1]

    def broke_upward(level: float, after_idx: int) -> bool:
        start = max(after_idx + 1, n - confirm_recent)
        return any(closes[j] > level for j in range(start, n))

    def broke_downward(level: float, after_idx: int) -> bool:
        start = max(after_idx + 1, n - confirm_recent)
        return any(closes[j] < level for j in range(start, n))

    event = None
    event_level = None

    up_break = broke_upward(last_h_px, last_h_idx)
    down_break = broke_downward(last_l_px, last_l_idx)

    if up_break and not down_break:
        event_level = last_h_px
        if trend == "BULLISH":
            event = "BOS"
        else:
            event = "CHOCH_BULL"
            trend = "BULLISH"
    elif down_break and not up_break:
        event_level = last_l_px
        if trend == "BEARISH":
            event = "BOS"
        else:
            event = "CHOCH_BEAR"
            trend = "BEARISH"

    rep.trend = trend
    rep.event = event
    rep.event_level = event_level
    return rep


def scan_price_action(df: pd.DataFrame | None) -> PriceActionReport | None:
    if df is None:
        return None
    try:
        return PriceActionReport(
            structure=scan_structure(df),
            liquidity=scan_liquidity(df),
        )
    except Exception:
        return None


def price_action_bonus(report: PriceActionReport | None, direction: str) -> int:
    """Yo'nalishga mos keladigan PA faktorlari uchun ishonch bonusi (-3..+7)."""
    if report is None or direction not in ("LONG", "SHORT"):
        return 0
    want = "BULLISH" if direction == "LONG" else "BEARISH"
    score = 0

    st = report.structure.trend
    ev = report.structure.event
    liq = report.liquidity

    if st == want:
        score += 3
    if ev == "BOS" and st == want:
        score += 2
    if ev == "CHOCH_BULL" and direction == "LONG":
        score += 2
    if ev == "CHOCH_BEAR" and direction == "SHORT":
        score += 2
    if getattr(liq, "swept_bullish", False) and direction == "LONG":
        score += 2
    if getattr(liq, "swept_bearish", False) and direction == "SHORT":
        score += 2

    if st != want and ev:
        score -= 3

    return max(-3, min(score, 7))


def pa_text(report: PriceActionReport | None, lang: str = "uz") -> str:
    """Xabarga qo'shiladigan ixcham PA bo'limi."""
    from indicators_engine import auto_decimals, fmt_price
    from utils.i18n import t

    if report is None:
        return ""

    st = report.structure
    liq = report.liquidity
    parts: list[str] = []

    trend_txt = {
        "uz": {"BULLISH": "Bullish 🟢", "BEARISH": "Bearish 🔴", "NEUTRAL": "Neytral ⚪️"},
        "ru": {"BULLISH": "Бычий 🟢", "BEARISH": "Медвежий 🔴", "NEUTRAL": "Нейтрально ⚪️"},
        "en": {"BULLISH": "Bullish 🟢", "BEARISH": "Bearish 🔴", "NEUTRAL": "Neutral ⚪️"},
    }[lang][st.trend]

    event_suffix = ""
    if st.event:
        event_suffix = {
            "BOS": {
                "uz": " · BOS (davom etishi)",
                "ru": " · BOS (продолжение)",
                "en": " · BOS (continuation)",
            },
            "CHOCH_BULL": {
                "uz": " · CHoCH ↑ (burilish)",
                "ru": " · CHoCH ↑ (разворот)",
                "en": " · CHoCH ↑ (reversal)",
            },
            "CHOCH_BEAR": {
                "uz": " · CHoCH ↓ (burilish)",
                "ru": " · CHoCH ↓ (разворот)",
                "en": " · CHoCH ↓ (reversal)",
            },
        }[lang][st.event]

    parts.append(f"🧭 {t(lang, 'pa_structure')}: <b>{trend_txt}{event_suffix}</b>")

    def _fmt_levels(pools: list[LiquidityPool]) -> str:
        if not pools:
            return "-"
        dec = auto_decimals(pools[0].price)
        return ", ".join(fmt_price(p.price, dec) for p in pools[:2])

    parts.append(
        t(
            lang,
            "pa_liquidity",
            above=_fmt_levels(liq.pools_above),
            below=_fmt_levels(liq.pools_below),
        )
    )

    if liq.swept_bullish:
        parts.append(f"⚡️ {t(lang, 'pa_sweep_bull')}")
    if liq.swept_bearish:
        parts.append(f"⚡️ {t(lang, 'pa_sweep_bear')}")

    header = f"{t(lang, 'pa_section')}\n" + "\n".join(parts)
    return header
