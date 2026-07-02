from __future__ import annotations
import aiosqlite
from datetime import date, datetime
from config import DB_PATH


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.db: aiosqlite.Connection | None = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        if self.db:
            await self.db.close()

    async def _create_tables(self):
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'user',
                sbercoins INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                location TEXT DEFAULT 'online',
                event_type TEXT DEFAULT 'online',
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, event_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT DEFAULT 'photo',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                comment TEXT DEFAULT '',
                coins_awarded INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            );
        """)
        await self.db.commit()

    # ── Users ──

    async def get_user(self, user_id: int) -> dict | None:
        async with self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def create_user(self, user_id: int, username: str, full_name: str):
        await self.db.execute(
            "INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        await self.db.commit()

    async def set_role(self, user_id: int, role: str):
        await self.db.execute(
            "UPDATE users SET role = ? WHERE id = ?", (role, user_id)
        )
        await self.db.commit()

    async def add_coins(self, user_id: int, amount: int):
        await self.db.execute(
            "UPDATE users SET sbercoins = sbercoins + ? WHERE id = ?",
            (amount, user_id),
        )
        await self.db.commit()

    async def get_all_users(self) -> list[dict]:
        async with self.db.execute("SELECT * FROM users ORDER BY registered_at") as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def search_users(self, query: str) -> list[dict]:
        async with self.db.execute(
            "SELECT * FROM users WHERE full_name LIKE ? OR username LIKE ?",
            (f"%{query}%", f"%{query}%"),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def get_leaderboard(self, limit: int = 20) -> list[dict]:
        async with self.db.execute(
            "SELECT full_name, sbercoins FROM users WHERE sbercoins > 0 ORDER BY sbercoins DESC LIMIT ?",
            (limit,),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    # ── Events ──

    async def get_events_page(self, page: int = 0, per_page: int = 5) -> list[dict]:
        offset = page * per_page
        async with self.db.execute(
            "SELECT * FROM events ORDER BY date, time LIMIT ? OFFSET ?",
            (per_page, offset),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def count_events(self) -> int:
        async with self.db.execute("SELECT COUNT(*) FROM events") as cur:
            return (await cur.fetchone())[0]

    async def get_event(self, event_id: int) -> dict | None:
        async with self.db.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_upcoming_events(self) -> list[dict]:
        today = date.today().isoformat()
        async with self.db.execute(
            "SELECT * FROM events WHERE date >= ? ORDER BY date, time",
            (today,),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def create_event(
        self, title: str, ev_date: str, ev_time: str,
        location: str = "online", event_type: str = "online", description: str = ""
    ):
        await self.db.execute(
            "INSERT INTO events (title, date, time, location, event_type, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, ev_date, ev_time, location, event_type, description),
        )
        await self.db.commit()

    async def update_event(self, event_id: int, **kwargs):
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [event_id]
        await self.db.execute(f"UPDATE events SET {fields} WHERE id = ?", values)
        await self.db.commit()

    async def delete_event(self, event_id: int):
        await self.db.execute("DELETE FROM registrations WHERE event_id = ?", (event_id,))
        await self.db.execute("DELETE FROM homework WHERE event_id = ?", (event_id,))
        await self.db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        await self.db.commit()

    # ── Registrations ──

    async def register_for_event(self, user_id: int, event_id: int) -> bool:
        try:
            await self.db.execute(
                "INSERT INTO registrations (user_id, event_id) VALUES (?, ?)",
                (user_id, event_id),
            )
            await self.db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def unregister_from_event(self, user_id: int, event_id: int) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM registrations WHERE user_id = ? AND event_id = ?",
            (user_id, event_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def is_registered(self, user_id: int, event_id: int) -> bool:
        async with self.db.execute(
            "SELECT 1 FROM registrations WHERE user_id = ? AND event_id = ?",
            (user_id, event_id),
        ) as cur:
            return await cur.fetchone() is not None

    async def get_user_events(self, user_id: int) -> list[dict]:
        async with self.db.execute(
            """SELECT e.* FROM events e
               JOIN registrations r ON e.id = r.event_id
               WHERE r.user_id = ?
               ORDER BY e.date, e.time""",
            (user_id,),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def get_event_participants(self, event_id: int) -> list[dict]:
        async with self.db.execute(
            """SELECT u.* FROM users u
               JOIN registrations r ON u.id = r.user_id
               WHERE r.event_id = ?
               ORDER BY u.full_name""",
            (event_id,),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    # ── Homework ──

    async def submit_homework(
        self, user_id: int, event_id: int, file_id: str, file_type: str = "photo"
    ):
        await self.db.execute(
            "INSERT INTO homework (user_id, event_id, file_id, file_type) VALUES (?, ?, ?, ?)",
            (user_id, event_id, file_id, file_type),
        )
        await self.db.commit()

    async def get_pending_homework(self) -> list[dict]:
        async with self.db.execute(
            """SELECT h.*, u.full_name, u.username, e.title as event_title
               FROM homework h
               JOIN users u ON h.user_id = u.id
               JOIN events e ON h.event_id = e.id
               WHERE h.status = 'pending'
               ORDER BY h.submitted_at"""
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def get_user_homework(self, user_id: int) -> list[dict]:
        async with self.db.execute(
            """SELECT h.*, e.title as event_title
               FROM homework h
               JOIN events e ON h.event_id = e.id
               WHERE h.user_id = ?
               ORDER BY h.submitted_at DESC""",
            (user_id,),
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]

    async def review_homework(self, hw_id: int, status: str, comment: str = "", coins: int = 0):
        await self.db.execute(
            "UPDATE homework SET status = ?, comment = ?, coins_awarded = ? WHERE id = ?",
            (status, comment, coins, hw_id),
        )
        await self.db.commit()

    async def get_homework_by_id(self, hw_id: int) -> dict | None:
        async with self.db.execute(
            "SELECT * FROM homework WHERE id = ?", (hw_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None
