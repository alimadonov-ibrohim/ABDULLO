import json
import urllib.request

update = {
    "update_id": 1,
    "message": {
        "message_id": 1,
        "date": 1700000000,
        "chat": {"id": 123456789, "type": "private", "first_name": "Test"},
        "from": {"id": 123456789, "is_bot": False, "first_name": "Test"},
        "text": "/start",
    },
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/webhook",
    data=json.dumps(update).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("WEBHOOK_RESPONSE:", resp.status, resp.read().decode())
except Exception as e:
    print("WEBHOOK_ERROR:", e)
