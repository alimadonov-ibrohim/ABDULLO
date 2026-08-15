import json
import re
import time
import ssl
import urllib.request

RATES_URL = "https://ipakyulibank.uz/physical/valyuta-ayirboshlash"
CACHE_TTL = 600

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

_cache = {"data": None, "ts": 0}


def _fetch_html():
    req = urllib.request.Request(RATES_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20, context=_ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _resolve(data, idx, depth=0):
    if depth > 80 or idx < 0 or idx >= len(data):
        return None
    node = data[idx]
    if isinstance(node, list) and len(node) == 2 and isinstance(node[0], str) and isinstance(node[1], int):
        kind, ref = node
        if kind in ("ShallowReactive", "Reactive", "Ref"):
            return _resolve(data, ref, depth + 1)
        if kind == "EmptyRef":
            return None
        return node
    if isinstance(node, list):
        out = []
        for item in node:
            if isinstance(item, int):
                out.append(_resolve(data, item, depth + 1))
            elif isinstance(item, list):
                out.append(_resolve(data, data.index(item), depth + 1))
            else:
                out.append(item)
        return out
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if isinstance(v, int):
                out[k] = _resolve(data, v, depth + 1)
            elif isinstance(v, list):
                out[k] = _resolve(data, data.index(v), depth + 1)
            else:
                out[k] = v
        return out
    return node


def get_rates(force=False):
    now = time.time()
    if not force and _cache["data"] and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    html = _fetch_html()
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("Valyuta ma'lumotlari sahifadan topilmadi")

    payload = json.loads(m.group(1))
    root = _resolve(payload, 2)

    component = None
    for key, value in root.items():
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, dict) and first.get("tabs"):
                for r in first["tabs"]:
                    if isinstance(r, dict) and r.get("rates"):
                        component = first
                        break
            if component:
                break

    if not component:
        raise RuntimeError("Kurslar komponenti topilmadi")

    tabs = []
    for tab in component["tabs"]:
        rates = []
        for r in tab["rates"]:
            rates.append({
                "code": r.get("code_name"),
                "iso": r.get("code"),
                "name": r.get("name"),
                "symbol": r.get("symbol"),
                "buy": r["rate"].get("buy"),
                "sell": r["rate"].get("sell"),
                "cb": r["rate"].get("cb"),
            })
        tabs.append({
            "name": tab.get("name"),
            "lastUpdated": tab.get("lastUpdated"),
            "rates": rates,
        })

    result = {"source": "ipakyulibank.uz", "tabs": tabs}
    _cache["data"] = result
    _cache["ts"] = now
    return result


def find_rate(tabs, code, tab_name=None):
    code = str(code).upper()
    for tab in tabs:
        if tab_name and tab["name"] != tab_name:
            continue
        for r in tab["rates"]:
            if r["code"] == code:
                return tab["name"], r
    return None, None


def convert(amount, currency, tab_name=None, side="buy"):
    data = get_rates()
    tab, rate = find_rate(data["tabs"], currency, tab_name)
    if not rate:
        raise ValueError(f"Bunday valyuta topilmadi: {currency}")

    value = rate.get(side)
    if not value:
        raise ValueError(f"'{side}' kursi mavjud emas")

    return {
        "from": rate["code"],
        "to": "UZS",
        "amount": amount,
        "rate": value,
        "result": round(amount * value / 100, 2),
        "tab": tab,
        "side": side,
    }