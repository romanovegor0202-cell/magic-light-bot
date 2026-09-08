import aiosqlite
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "magic_light.db"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    event_date TEXT NOT NULL,
    venue TEXT NOT NULL,
    comment TEXT,
    items_json TEXT NOT NULL,
    total_min INTEGER NOT NULL,
    total_max INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_SQL)
        await db.commit()

async def get_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT product_id, quantity FROM cart WHERE user_id=?", (user_id,))
        return [dict(row) for row in await cur.fetchall()]

async def set_cart_item(user_id: int, product_id: str, quantity: int):
    async with aiosqlite.connect(DB_PATH) as db:
        if quantity <= 0:
            await db.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
        else:
            await db.execute(
                "INSERT INTO cart(user_id,product_id,quantity) VALUES(?,?,?) "
                "ON CONFLICT(user_id,product_id) DO UPDATE SET quantity=excluded.quantity",
                (user_id, product_id, quantity),
            )
        await db.commit()

async def clear_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        await db.commit()

async def create_order(user_id: int, username: Optional[str], name: str, phone: str,
                      event_date: str, venue: str, comment: str, items_json: str,
                      total_min: int, total_max: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders(user_id,username,name,phone,event_date,venue,comment,items_json,total_min,total_max) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (user_id, username, name, phone, event_date, venue, comment, items_json, total_min, total_max),
        )
        await db.commit()
        return cur.lastrowid
