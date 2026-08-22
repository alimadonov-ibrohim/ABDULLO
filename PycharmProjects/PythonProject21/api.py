from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse

import ipakyuli_api

app = FastAPI(title="Valyuta kurslari mini API", version="1.0")

BASE_DIR = Path(__file__).parent
WEBAPP_FILE = BASE_DIR / "webapp.html"


@app.get("/")
def index():
    return {"service": "Ipak Yuli valyuta mini API", "docs": "/docs", "endpoints": ["/rates", "/convert", "/webapp"]}


@app.get("/rates")
def rates(force: bool = False):
    try:
        return ipakyuli_api.get_rates(force=force)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/convert")
def convert(
    amount: float = Query(..., gt=0, description="Summa (valyutada)"),
    currency: str = Query(..., description="Valyuta kodi: USD, EUR, RUB, GBP, CHF, JPY"),
    tab: str = Query("Kassada", description="Kurs turi: Kassada, Bankomatda, Ilovada"),
    side: str = Query("buy", description="buy yoki sell"),
):
    try:
        return ipakyuli_api.convert(amount, currency, tab, side)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/webapp", response_class=FileResponse)
def webapp():
    return WEBAPP_FILE


@app.post("/webhook")
async def webhook(request: Request):
    import bot

    payload = await request.json()
    try:
        await bot.handle_update(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)