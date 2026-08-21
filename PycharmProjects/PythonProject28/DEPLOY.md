# Deploy qilish (Railway / Render)

Bu bot long polling bilan ishlaydi — doimiy ishlaydigan server kerak.
Vercel mos emas!

## 1-usul: Railway (eng oson)

1. https://railway.app → GitHub bilan kiring
2. **New Project** → **Deploy from GitHub repo** → `alimadonov-ibrohim/ABDULLO` tanlang
3. Service → **Settings**:
   - **Root Directory**: `PycharmProjects/PythonProject28`
   - **Start Command**: `python main.py`
4. **Variables** bo'limiga 4 ta env var qo'shing:
   ```
   API_ID=207475
   API_HASH=...
   BOT_TOKEN=...
   PYTHON_VERSION=3.11.9
   ```
5. Deploy — bot doimiy ishlaydi.

## 2-usul: Render

1. https://render.com → GitHub bilan kiring
2. **New** → **Worker** (Web Service emas!)
3. Repo: `alimadonov-ibrohim/ABDULLO`
   - **Root Directory**: `PycharmProjects/PythonProject28`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
4. **Environment** bo'limida `API_ID`, `API_HASH`, `BOT_TOKEN` va `PYTHON_VERSION=3.11.9` qo'shing
5. **Create Worker**

## Muhim

- Python **3.11** bo'lishi shart (`PYTHON_VERSION=3.11.9`) — aiogram 2.x yangi Python'larda o'rnatilmaydi

## Eslatma

- `.env` fayl serverga yuklanmaydi — tokenlar env var orqali beriladi
- `.sesiya/` papkasi serverda avtomatik yaratiladi
- Railway'da bepul kredit tugasa, kartani ulash yoki VPS o'tkazish kerak
