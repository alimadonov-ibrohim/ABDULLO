import asyncio
from datetime import datetime, timedelta, timezone

import aiosqlite

import config


class Database:
    def __init__(self, path: str = config.DB_PATH):
        self._path = path
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                full_name     TEXT,
                joined_at     TEXT NOT NULL,
                requests      INTEGER NOT NULL DEFAULT 0,
                notifications INTEGER NOT NULL DEFAULT 1,
                is_banned     INTEGER NOT NULL DEFAULT 0,
                language      TEXT
            );

            CREATE TABLE IF NOT EXISTS vip_subscriptions (
                user_id    INTEGER PRIMARY KEY REFERENCES users(user_id),
                until      TEXT NOT NULL,
                plan       TEXT DEFAULT 'manual',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS signals (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER REFERENCES users(user_id),
                symbol     TEXT NOT NULL,
                direction  TEXT NOT NULL,
                timeframe  TEXT NOT NULL,
                entry      REAL,
                sl         REAL,
                tp1        REAL,
                tp2        REAL,
                tp3        REAL,
                confidence REAL NOT NULL,
                rr_ratio   REAL,
                source     TEXT NOT NULL DEFAULT 'manual',
                status     TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol, direction);
            CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);
            """
        )
        await self._migrate()
        await self._conn.commit()

    async def _migrate(self) -> None:
        """Eski bazaga yangi ustunlarni qo'shadi (mavjud bo'lmasa)."""
        cur = await self.conn.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in await cur.fetchall()}
        if "language" not in cols:
            await self.conn.execute("ALTER TABLE users ADD COLUMN language TEXT")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    async def upsert_user(
        self, user_id: int, username: str | None, full_name: str | None
    ) -> None:
        async with self._lock:
            await self.conn.execute(
                """
                INSERT INTO users (user_id, username, full_name, joined_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username  = COALESCE(excluded.username, users.username),
                    full_name = COALESCE(excluded.full_name, users.full_name)
                """,
                (user_id, username, full_name, self._now_iso()),
            )
            await self.conn.commit()

    async def increment_requests(self, user_id: int) -> None:
        async with self._lock:
            await self.conn.execute(
                "UPDATE users SET requests = requests + 1 WHERE user_id = ?",
                (user_id,),
            )
            await self.conn.commit()

    async def get_user(self, user_id: int) -> dict | None:
        cur = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def all_user_ids(self) -> list[int]:
        cur = await self.conn.execute(
            "SELECT user_id FROM users WHERE is_banned = 0 ORDER BY user_id"
        )
        return [r[0] for r in await cur.fetchall()]

    async def count_users(self) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) FROM users")
        return (await cur.fetchone())[0]

    async def set_banned(self, user_id: int, banned: bool) -> bool:
        async with self._lock:
            cur = await self.conn.execute(
                "UPDATE users SET is_banned = ? WHERE user_id = ?",
                (int(banned), user_id),
            )
            await self.conn.commit()
        return cur.rowcount > 0

    async def set_language(self, user_id: int, lang: str) -> None:
        from utils.i18n import SUPPORTED_LANGS

        if lang not in SUPPORTED_LANGS:
            lang = "uz"
        async with self._lock:
            await self.conn.execute(
                "UPDATE users SET language = ? WHERE user_id = ?",
                (lang, user_id),
            )
            await self.conn.commit()

    async def get_language(self, user_id: int) -> str | None:
        cur = await self.conn.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else None

    async def recent_users(self, limit: int = 10) -> list[dict]:
        cur = await self.conn.execute(
            """
            SELECT user_id, username, full_name, joined_at, is_banned
            FROM users ORDER BY joined_at DESC LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def banned_users(self, limit: int = 20) -> list[dict]:
        cur = await self.conn.execute(
            """
            SELECT user_id, username, full_name, joined_at
            FROM users WHERE is_banned = 1
            ORDER BY user_id LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def count_banned(self) -> int:
        cur = await self.conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        return (await cur.fetchone())[0]

    async def set_vip(self, user_id: int, days: int, plan: str = "manual") -> str:
        now = datetime.now(timezone.utc)
        current = await self.get_vip_until(user_id)
        base = max(now, current) if current else now
        until = base + timedelta(days=days)
        iso = until.isoformat(timespec="seconds")
        async with self._lock:
            await self.conn.execute(
                """
                INSERT INTO vip_subscriptions (user_id, until, plan, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    until = excluded.until,
                    plan = excluded.plan,
                    updated_at = excluded.updated_at
                """,
                (user_id, iso, plan, self._now_iso()),
            )
            await self.conn.commit()
        return iso

    async def revoke_vip(self, user_id: int) -> bool:
        async with self._lock:
            cur = await self.conn.execute(
                "DELETE FROM vip_subscriptions WHERE user_id = ?", (user_id,)
            )
            await self.conn.commit()
        return cur.rowcount > 0

    async def get_vip_until(self, user_id: int) -> datetime | None:
        cur = await self.conn.execute(
            "SELECT until FROM vip_subscriptions WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        try:
            return datetime.fromisoformat(row[0])
        except ValueError:
            return None

    async def is_vip(self, user_id: int) -> bool:
        if user_id in config.ADMIN_IDS:
            return True
        until = await self.get_vip_until(user_id)
        return bool(until and until > datetime.now(timezone.utc))

    async def active_vip_user_ids(self) -> list[int]:
        cur = await self.conn.execute("SELECT user_id, until FROM vip_subscriptions")
        rows = await cur.fetchall()
        now = datetime.now(timezone.utc)
        ids = []
        for r in rows:
            try:
                if datetime.fromisoformat(r["until"]) > now:
                    ids.append(r["user_id"])
            except ValueError:
                continue
        for admin in config.ADMIN_IDS:
            if admin not in ids:
                ids.append(admin)
        return ids

    async def save_signal(self, data: dict) -> int:
        async with self._lock:
            cur = await self.conn.execute(
                """
                INSERT INTO signals (
                    user_id, symbol, direction, timeframe, entry, sl,
                    tp1, tp2, tp3, confidence, rr_ratio, source, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """,
                (
                    data.get("user_id"),
                    data["symbol"],
                    data["direction"],
                    data["timeframe"],
                    data.get("entry"),
                    data.get("sl"),
                    data.get("tp1"),
                    data.get("tp2"),
                    data.get("tp3"),
                    data["confidence"],
                    data.get("rr_ratio"),
                    data.get("source", "manual"),
                    self._now_iso(),
                ),
            )
            await self.conn.commit()
            return cur.lastrowid

    async def recent_signals(self, limit: int = 10, only_auto: bool = False) -> list[dict]:
        query = "SELECT * FROM signals"
        params: tuple = ()
        if only_auto:
            query += " WHERE source = 'auto'"
        query += " ORDER BY created_at DESC LIMIT ?"
        params = (*params, limit)
        cur = await self.conn.execute(query, params)
        return [dict(r) for r in await cur.fetchall()]

    async def last_signal_time(self, symbol: str, direction: str, hours: int) -> datetime | None:
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(
            timespec="seconds"
        )
        cur = await self.conn.execute(
            """
            SELECT created_at FROM signals
            WHERE symbol = ? AND direction = ? AND source = 'auto' AND created_at >= ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (symbol, direction, since),
        )
        row = await cur.fetchone()
        if not row:
            return None
        try:
            return datetime.fromisoformat(row[0])
        except ValueError:
            return None

    async def stats_summary(self) -> dict:
        total_cur = await self.conn.execute("SELECT COUNT(*) FROM signals")
        total = (await total_cur.fetchone())[0]
        dir_cur = await self.conn.execute(
            """
            SELECT direction, COUNT(*) AS cnt FROM signals
            GROUP BY direction
            """
        )
        by_direction = {r["direction"]: r["cnt"] for r in await dir_cur.fetchall()}
        conf_cur = await self.conn.execute(
            "SELECT AVG(confidence) FROM signals WHERE confidence IS NOT NULL"
        )
        avg_conf = (await conf_cur.fetchone())[0] or 0.0
        top_cur = await self.conn.execute(
            """
            SELECT symbol, COUNT(*) AS cnt FROM signals
            GROUP BY symbol ORDER BY cnt DESC LIMIT 5
            """
        )
        top_symbols = {r["symbol"]: r["cnt"] for r in await top_cur.fetchall()}
        today = datetime.now(timezone.utc).date().isoformat()
        day_cur = await self.conn.execute(
            "SELECT COUNT(*) FROM signals WHERE substr(created_at, 1, 10) = ?", (today,)
        )
        today_count = (await day_cur.fetchone())[0]
        return {
            "total_signals": total,
            "today_signals": today_count,
            "buy": by_direction.get("LONG", 0),
            "sell": by_direction.get("SHORT", 0),
            "avg_confidence": round(float(avg_conf), 1),
            "top_symbols": top_symbols,
            "total_users": await self.count_users(),
        }


db = Database()
