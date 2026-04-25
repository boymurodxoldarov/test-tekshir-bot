"""
database.py — Async SQLite layer.
Tests, users, results — barchasi shu yerda.
"""
import logging
from typing import Optional

import aiosqlite

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────
CREATE_TABLES = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    UNIQUE NOT NULL,
    answers     TEXT    NOT NULL,
    created_by  INTEGER NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    name        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    test_code  TEXT    NOT NULL,
    score      INTEGER NOT NULL,
    total      INTEGER NOT NULL,
    answers    TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_test ON results(test_code);
CREATE INDEX IF NOT EXISTS idx_tests_code   ON tests(code);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.executescript(CREATE_TABLES)
        await db.commit()
    logger.info("DB ready: %s", DATABASE_URL)


# ─────────────────────────────────────────────
# Tests CRUD
# ─────────────────────────────────────────────
async def add_test(code: str, answers: str, created_by: int) -> bool:
    """True = yangi, False = yangilandi."""
    code = code.upper().strip()
    answers = answers.lower().replace(" ", "").strip()
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute("SELECT id FROM tests WHERE code = ?", (code,))
        existing = await cur.fetchone()
        if existing:
            await db.execute(
                "UPDATE tests SET answers = ?, created_by = ?, created_at = datetime('now') WHERE code = ?",
                (answers, created_by, code),
            )
            await db.commit()
            return False
        else:
            await db.execute(
                "INSERT INTO tests (code, answers, created_by) VALUES (?, ?, ?)",
                (code, answers, created_by),
            )
            await db.commit()
            return True


async def delete_test(code: str) -> bool:
    """True = o'chirildi, False = topilmadi."""
    code = code.upper().strip()
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute("DELETE FROM tests WHERE code = ?", (code,))
        await db.commit()
        return cur.rowcount > 0


async def get_test(code: str) -> Optional[str]:
    """Test kalitini qaytaradi yoki None."""
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            "SELECT answers FROM tests WHERE code = ?", (code.upper(),)
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def get_all_tests() -> list[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            "SELECT code, answers, created_at FROM tests ORDER BY code"
        )
        rows = await cur.fetchall()
        return [{"code": r[0], "answers": r[1], "created_at": r[2]} for r in rows]


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────
async def get_or_create_user(telegram_id: int, name: str) -> int:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cur.fetchone()
        if row:
            # Ismni yangilab ketamiz
            await db.execute(
                "UPDATE users SET name = ? WHERE telegram_id = ?", (name, telegram_id)
            )
            await db.commit()
            return row[0]
        cur = await db.execute(
            "INSERT INTO users (telegram_id, name) VALUES (?, ?)", (telegram_id, name)
        )
        await db.commit()
        return cur.lastrowid


async def get_total_users() -> int:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        return (await cur.fetchone())[0]


# ─────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────
async def save_result(
    user_id: int, test_code: str, score: int, total: int, answers: str
) -> int:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            """INSERT INTO results (user_id, test_code, score, total, answers)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, test_code.upper(), score, total, answers),
        )
        await db.commit()
        return cur.lastrowid


async def get_user_stats(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            """SELECT
                 COUNT(*)                                           AS attempts,
                 MAX(CAST(r.score AS REAL) / r.total * 100)        AS best_pct,
                 AVG(CAST(r.score AS REAL) / r.total * 100)        AS avg_pct,
                 MAX(r.score)                                       AS best_score,
                 (SELECT r2.total FROM results r2
                  JOIN users u2 ON u2.id = r2.user_id
                  WHERE u2.telegram_id = ?
                  ORDER BY CAST(r2.score AS REAL)/r2.total DESC LIMIT 1) AS best_total,
                 (SELECT r2.test_code FROM results r2
                  JOIN users u2 ON u2.id = r2.user_id
                  WHERE u2.telegram_id = ?
                  ORDER BY CAST(r2.score AS REAL)/r2.total DESC LIMIT 1) AS best_test
               FROM results r
               JOIN users u ON u.id = r.user_id
               WHERE u.telegram_id = ?""",
            (telegram_id, telegram_id, telegram_id),
        )
        row = await cur.fetchone()
        if not row or row[0] == 0:
            return None
        return {
            "attempts":   row[0],
            "best_pct":   round(row[1], 1),
            "avg_pct":    round(row[2], 1),
            "best_score": row[3],
            "best_total": row[4],
            "best_test":  row[5],
        }


async def get_user_history(telegram_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            """SELECT r.test_code, r.score, r.total, r.created_at
               FROM results r
               JOIN users u ON u.id = r.user_id
               WHERE u.telegram_id = ?
               ORDER BY r.created_at DESC
               LIMIT ?""",
            (telegram_id, limit),
        )
        rows = await cur.fetchall()
        return [
            {"test_code": r[0], "score": r[1], "total": r[2], "created_at": r[3]}
            for r in rows
        ]


async def get_leaderboard(test_code: str, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DATABASE_URL) as db:
        cur = await db.execute(
            """SELECT
                 u.name,
                 MAX(r.score)  AS best_score,
                 r.total,
                 COUNT(*)      AS attempts
               FROM results r
               JOIN users u ON u.id = r.user_id
               WHERE r.test_code = ?
               GROUP BY r.user_id
               ORDER BY best_score DESC, r.total ASC
               LIMIT ?""",
            (test_code.upper(), limit),
        )
        rows = await cur.fetchall()
        return [
            {"name": r[0], "score": r[1], "total": r[2], "attempts": r[3]}
            for r in rows
        ]


async def get_admin_stats() -> dict:
    async with aiosqlite.connect(DATABASE_URL) as db:
        c1 = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await c1.fetchone())[0]

        c2 = await db.execute("SELECT COUNT(*) FROM results")
        total_submissions = (await c2.fetchone())[0]

        c3 = await db.execute("SELECT COUNT(*) FROM tests")
        total_tests = (await c3.fetchone())[0]

        c4 = await db.execute(
            "SELECT AVG(CAST(score AS REAL) / total * 100) FROM results"
        )
        row = await c4.fetchone()
        avg_pct = round(row[0], 1) if row and row[0] is not None else 0.0

        c5 = await db.execute(
            """SELECT test_code, COUNT(*) as cnt
               FROM results GROUP BY test_code
               ORDER BY cnt DESC LIMIT 1"""
        )
        popular = await c5.fetchone()

        return {
            "total_users":       total_users,
            "total_submissions": total_submissions,
            "total_tests":       total_tests,
            "avg_pct":           avg_pct,
            "popular_test":      popular[0] if popular else "—",
            "popular_count":     popular[1] if popular else 0,
        }
