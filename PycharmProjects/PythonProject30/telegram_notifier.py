"""
Telegram bot orqali signal xabarlarini yuborish, til tanlash tugmalarini
ko'rsatish va foydalanuvchi xabarlarini qabul qilish moduli.
"""
import requests

from locales import SIGNAL_LABELS, LANGUAGE_BUTTONS


class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: str = None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, chat_id: str = None, reply_markup: dict = None):
        chat_id = chat_id or self.default_chat_id
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            import json as _json
            payload["reply_markup"] = _json.dumps(reply_markup)
        try:
            response = requests.post(f"{self.api_url}/sendMessage", data=payload, timeout=10)
            if response.status_code != 200:
                print(f"[Telegram xatosi] {response.text}")
        except Exception as e:
            print(f"[Telegram yuborishda xatolik] {e}")

    def send_language_selector(self, chat_id: str, welcome_text: str):
        """Til tanlash uchun inline tugmalarni yuboradi."""
        keyboard = {
            "inline_keyboard": [
                [{"text": btn["text"], "callback_data": btn["callback_data"]}]
                for btn in LANGUAGE_BUTTONS
            ]
        }
        self.send_message(welcome_text, chat_id=chat_id, reply_markup=keyboard)

    def answer_callback_query(self, callback_query_id: str, text: str = ""):
        """Tugma bosilganda Telegram'ga 'qabul qilindi' signalini beradi (soat belgisi yo'qolishi uchun)."""
        try:
            requests.post(
                f"{self.api_url}/answerCallbackQuery",
                data={"callback_query_id": callback_query_id, "text": text},
                timeout=10,
            )
        except Exception as e:
            print(f"[answerCallbackQuery xatosi] {e}")

    def build_pair_keyboard(self, available_symbols: list, selected: list) -> dict:
        """Juftlik tanlash inline tugmalarini yig'adi."""
        rows = []
        for sym in available_symbols:
            mark = "✅" if sym in selected else "▫️"
            rows.append([{"text": f"{mark} {sym}", "callback_data": f"sym_{sym}"}])
        return {"inline_keyboard": rows}

    def send_pair_selector(self, chat_id: str, text: str, keyboard: dict):
        self.send_message(text, chat_id=chat_id, reply_markup=keyboard)

    def edit_pair_keyboard(self, chat_id: str, message_id: int, keyboard: dict):
        """Tugma bosilgach, xabardagi belgilashlarni yangilaydi (yangi xabar yubormasdan)."""
        import json as _json
        try:
            requests.post(
                f"{self.api_url}/editMessageReplyMarkup",
                data={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "reply_markup": _json.dumps(keyboard),
                },
                timeout=10,
            )
        except Exception as e:
            print(f"[editMessageReplyMarkup xatosi] {e}")

    def get_updates(self, offset: int = None, timeout: int = 5):
        """Foydalanuvchidan kelgan yangi xabarlar/tugma bosishlarni oladi (long polling)."""
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            response = requests.get(f"{self.api_url}/getUpdates", params=params, timeout=timeout + 10)
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
            return []
        except Exception as e:
            print(f"[Telegram getUpdates xatosi] {e}")
            return []

    def format_signal_message(self, symbol: str, signal: str, details: dict, lang: str = "uz") -> str:
        labels = SIGNAL_LABELS.get(lang, SIGNAL_LABELS["uz"])
        emoji = "🟢" if signal == "BUY" else "🔴"
        signal_label = labels["BUY"] if signal == "BUY" else labels["SELL"]

        text = (
            f"{emoji} <b>{signal_label}</b>\n"
            f"📊 {labels['pair']}: <b>{symbol}</b>\n"
            f"💰 {labels['entry']}: {details['close']}\n"
            f"───────────────\n"
            f"🛑 {labels['sl']}: <b>{details.get('stop_loss', '-')}</b>\n"
            f"🎯 {labels['tp']}: <b>{details.get('take_profit', '-')}</b>\n"
            f"⚖️ {labels['rr']}: 1:{details.get('risk_reward', '-')}\n"
            f"───────────────\n"
            f"SMA9: {details['sma9']}  |  SMA50: {details['sma50']}\n"
            f"EMA200: {details['ema200']}\n"
            f"RSI: {details['rsi']}\n"
            f"MACD: {details['macd']} / Signal: {details['macd_signal']}\n"
            f"{labels['trend_strength']} (ADX): {details['adx']}\n"
            f"───────────────\n"
            f"{labels['disclaimer']}"
        )
        return text
