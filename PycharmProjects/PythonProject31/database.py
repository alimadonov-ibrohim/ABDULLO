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

            CREATE TABLE IF NOT EXISTS payments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                username    TEXT,
                full_name   TEXT,
                plan        TEXT NOT NULL,
                amount_usd  REAL,
                method      TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                payload     TEXT,
                created_at  TEXT NOT NULL,
                resolved_at TEXT,
                resolved_by INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status, created_at DESC);
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

        sig_cur = await self.conn.execute("PRAGMA table_info(signals)")
        sig_cols = {row[1] for row in await sig_cur.fetchall()}
        if "tp_hits" not in sig_cols:
            await self.conn.execute(
                "ALTER TABLE signals ADD COLUMN tp_hits INTEGER NOT NULL DEFAULT 0"
            )
        if "resolved_at" not in sig_cols:
            await self.conn.execute(
                "ALTER TABLE signals ADD COLUMN resolved_at TEXT"
            )

        ucur = await self.conn.execute("PRAGMA table_info(users)")
        ucols = {row[1] for row in await ucur.fetchall()}
        for col, decl in (
            ("trial_started", "TEXT"),
            ("trial_date", "TEXT"),
            ("trial_count", "INTEGER NOT NULL DEFAULT 0"),
            ("trial_notice_date", "TEXT"),
        ):
            if col not in ucols:
                await self.conn.execute(
                    f"ALTER TABLE users ADD COLUMN {col} {decl}"
                )

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

    # ---------------- sinov (trial) rejimi ----------------

    async def activate_trial(self, user_id: int) -> bool:
        """Birinchi /start'da trialni yoqadi (avval faollashmagan bo'lsa)."""
        import config

        if user_id in config.ADMIN_IDS:
            return False
        async with self._lock:
            cur = await self.conn.execute(
                """
                UPDATE users SET trial_started = ?
                WHERE user_id = ? AND trial_started IS NULL
                """,
                (self._now_iso(), user_id),
            )
            await self.conn.commit()
        return cur.rowcount > 0

    async def _trial_row(self, user_id: int) -> dict | None:
        cur = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    def _trial_days_left(self, trial_started: str | None) -> int:
        import config

        if not trial_started:
            return 0
        try:
            started = datetime.fromisoformat(trial_started)
        except ValueError:
            return 0
        elapsed = datetime.now(timezone.utc) - started
        left = config.TRIAL_DAYS - elapsed.days
        return max(left, 0)

    async def trial_status(self, user_id: int) -> dict | None:
        """VIP bo'lmasa: {'active': bool, 'days_left': n}. VIP/admin — None."""
        import config

        if user_id in config.ADMIN_IDS or await self.is_vip(user_id):
            return None
        row = await self._trial_row(user_id)
        if not row or not row["trial_started"] or row["is_banned"]:
            return {"active": False, "days_left": 0}
        days_left = self._trial_days_left(row["trial_started"])
        return {"active": days_left > 0, "days_left": days_left}

    async def active_trial_ids(self) -> list[int]:
        cur = await self.conn.execute(
            "SELECT user_id, is_banned, trial_started FROM users "
            "WHERE trial_started IS NOT NULL"
        )
        now = datetime.now(timezone.utc)
        vip_ids = set(await self.active_vip_user_ids())
        ids = []
        for r in await cur.fetchall():
            uid = r["user_id"]
            if r["is_banned"] or uid in vip_ids or uid in ids:
                continue
            try:
                started = datetime.fromisoformat(r["trial_started"])
            except (ValueError, TypeError):
                continue
            if (now - started).days < config.TRIAL_DAYS:
                ids.append(uid)
        return ids

    async def try_consume_trial_slot(self, user_id: int) -> bool:
        """Kunlik bepul slot bor-bo'lg'usini sarflaydi. True = signal yubor."""
        import config

        row = await self._trial_row(user_id)
        if not row or not row["trial_started"] or row["is_banned"]:
            return False
        if self._trial_days_left(row["trial_started"]) <= 0:
            return False

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        count = int(row["trial_count"] or 0)
        date = row["trial_date"]

        if date != today:
            count = 0

        if count >= config.TRIAL_DAILY_SIGNALS:
            return False

        async with self._lock:
            await self.conn.execute(
                """
                UPDATE users
                SET trial_date = ?, trial_count = ?
                WHERE user_id = ?
                """,
                (today, count + 1, user_id),
            )
            await self.conn.commit()
        return True

    async def should_notify_trial_limit(self, user_id: int) -> bool:
        """Kuniga bir marta 'limit tugadi' xabari uchun ruxsat."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        row = await self._trial_row(user_id)
        if row and row["trial_notice_date"] == today:
            return False
        async with self._lock:
            await self.conn.execute(
                "UPDATE users SET trial_notice_date = ? WHERE user_id = ?",
                (today, user_id),
            )
            await self.conn.commit()
        return True

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

    async def list_active_vips(self, limit: int = 30) -> list[dict]:
        cur = await self.conn.execute(
            """
            SELECT v.user_id, v.until, v.plan,
                   u.username, u.full_name, u.is_banned
            FROM vip_subscriptions v
            LEFT JOIN users u ON u.user_id = v.user_id
            ORDER BY v.until DESC
            """
        )
        now = datetime.now(timezone.utc)
        out = []
        for r in await cur.fetchall():
            try:
                until = datetime.fromisoformat(r["until"])
            except ValueError:
                continue
            if until > now and len(out) < limit:
                d = dict(r)
                d["days_left"] = max((until - now).days, 0)
                out.append(d)
        return out

    async def count_trials(self) -> int:
        return len(await self.active_trial_ids())

    # ---------------- to'lovlar ----------------

    async def create_payment(
        self,
        user_id: int,
        plan: str,
        amount_usd: float,
        method: str,
        username: str | None = None,
        full_name: str | None = None,
        payload: str | None = None,
        status: str = "pending",
    ) -> int:
        async with self._lock:
            cur = await self.conn.execute(
                """
                INSERT INTO payments (
                    user_id, username, full_name, plan, amount_usd,
                    method, status, payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    full_name,
                    plan,
                    amount_usd,
                    method,
                    status,
                    payload,
                    self._now_iso(),
                ),
            )
            await self.conn.commit()
        return cur.lastrowid

    async def get_payment(self, payment_id: int) -> dict | None:
        cur = await self.conn.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def set_payment_status(
        self, payment_id: int, status: str, resolved_by: int | None = None
    ) -> bool:
        async with self._lock:
            cur = await self.conn.execute(
                """
                UPDATE payments
                SET status = ?, resolved_at = ?, resolved_by = ?
                WHERE id = ?
                """,
                (status, self._now_iso(), resolved_by, payment_id),
            )
            await self.conn.commit()
        return cur.rowcount > 0

    async def set_payment_payload(self, payment_id: int, payload: str) -> None:
        async with self._lock:
            await self.conn.execute(
                "UPDATE payments SET payload = ? WHERE id = ?",
                (payload, payment_id),
            )
            await self.conn.commit()

    async def pending_payments(self, limit: int = 20) -> list[dict]:
        cur = await self.conn.execute(
            """
            SELECT * FROM payments WHERE status = 'pending'
            ORDER BY created_at DESC LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def count_pending_payments(self) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*) FROM payments WHERE status = 'pending'"
        )
        return (await cur.fetchone())[0]

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

    async def open_auto_signals(self, limit: int = 100) -> list[dict]:
        cur = await self.conn.execute(
            """
            SELECT id, symbol, direction, entry, sl, tp1, tp2, tp3,
                   created_at, tp_hits
            FROM signals
            WHERE source = 'auto' AND status IN ('open', 'running')
            ORDER BY created_at ASC LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def set_signal_progress(
        self, signal_id: int, status: str, tp_hits: int, resolved_at: str | None = None
    ) -> None:
        async with self._lock:
            await self.conn.execute(
                """
                UPDATE signals
                SET status = ?, tp_hits = ?,
                    resolved_at = COALESCE(?, resolved_at)
                WHERE id = ?
                """,
                (status, tp_hits, resolved_at, signal_id),
            )
            await self.conn.commit()

    async def winrate_summary(self) -> dict:
        cur = await self.conn.execute(
            """
            SELECT status, COUNT(*) AS cnt
            FROM signals
            WHERE source = 'auto' AND status IN ('won', 'lost', 'running', 'open')
            GROUP BY status
            """
        )
        by_status = {r["status"]: r["cnt"] for r in await cur.fetchall()}
        won = by_status.get("won", 0)
        lost = by_status.get("lost", 0)
        closed = won + lost
        avg_cur = await self.conn.execute(
            "SELECT AVG(tp_hits) FROM signals WHERE source='auto' AND status='won'"
        )
        avg_tp = (await avg_cur.fetchone())[0] or 0.0
        return {
            "won": won,
            "lost": lost,
            "closed": closed,
            "running": by_status.get("running", 0),
            "open": by_status.get("open", 0),
            "winrate_pct": round(won * 100 / closed, 1) if closed else None,
            "avg_tp_reached": round(float(avg_tp), 1),
        }

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
