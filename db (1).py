import sqlite3
import time
import json
from typing import Optional, List, Dict, Any

DB_PATH = "game.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._seed_defaults()

    def _init_tables(self):
        c = self.conn.cursor()

        c.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            coins INTEGER DEFAULT 0,
            referrer_id INTEGER,
            last_mine_time REAL DEFAULT 0,
            created_at REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '📦',
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            base_profit INTEGER DEFAULT 100,
            base_cost INTEGER DEFAULT 1000,
            image_file_id TEXT DEFAULT '',
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS user_cards (
            user_id INTEGER,
            card_id INTEGER,
            level INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, card_id)
        );

        CREATE TABLE IF NOT EXISTS character_images (
            key TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS card_images (
            card_id INTEGER,
            level INTEGER,
            file_id TEXT,
            PRIMARY KEY (card_id, level)
        );

        CREATE TABLE IF NOT EXISTS level_thresholds (
            level INTEGER PRIMARY KEY,
            min_coins INTEGER NOT NULL
        );
        """)
        self.conn.commit()

    def _seed_defaults(self):
        c = self.conn.cursor()

        # تنظیمات پیش‌فرض
        defaults = {
            "bot_name": "Space Coin",
            "coins_per_tap": "1",
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

        # سطوح پیش‌فرض
        levels = [
            (1, 0), (2, 10000), (3, 50000), (4, 200000),
            (5, 500000), (6, 1000000), (7, 5000000),
            (8, 10000000), (9, 50000000), (10, 100000000),
        ]
        for lvl, coins in levels:
            c.execute("INSERT OR IGNORE INTO level_thresholds (level, min_coins) VALUES (?, ?)", (lvl, coins))

        # دسته‌بندی پیش‌فرض
        cats = [
            ("فناوری", "💻"), ("کیهان", "🌌"), ("انرژی", "⚡"), ("تجارت", "💼")
        ]
        for name, icon in cats:
            c.execute("INSERT OR IGNORE INTO categories (name, icon) SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name=?)", (name, icon, name))

        # کارت‌های پیش‌فرض
        c.execute("SELECT id FROM categories LIMIT 1")
        row = c.fetchone()
        if row:
            cat_id = row[0]
            sample_cards = [
                ("ماهواره", 500, 5000, cat_id),
                ("ایستگاه فضایی", 1500, 20000, cat_id),
                ("موتور یونی", 3000, 50000, cat_id),
            ]
            for name, profit, cost, cid in sample_cards:
                c.execute("INSERT OR IGNORE INTO cards (name, base_profit, base_cost, category_id) SELECT ?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM cards WHERE name=?)",
                          (name, profit, cost, cid, name))

        self.conn.commit()

    # ── Settings ──────────────────────────────────────
    def get_settings(self) -> Dict:
        c = self.conn.cursor()
        c.execute("SELECT key, value FROM settings")
        return {r["key"]: r["value"] for r in c.fetchall()}

    def set_setting(self, key: str, value: str):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    # ── Users ──────────────────────────────────────────
    def get_user(self, user_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return dict(row) if row else None

    def create_user(self, user_id: int, username: str, first_name: str, referrer_id=None):
        self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, referrer_id, created_at) VALUES (?,?,?,?,?)",
            (user_id, username, first_name, referrer_id, time.time())
        )
        self.conn.commit()

    def add_coins(self, user_id: int, amount: int):
        self.conn.execute("UPDATE users SET coins = MAX(0, coins + ?) WHERE user_id = ?", (amount, user_id))
        self.conn.commit()

    def update_last_mine(self, user_id: int):
        self.conn.execute("UPDATE users SET last_mine_time = ? WHERE user_id = ?", (time.time(), user_id))
        self.conn.commit()

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM users ORDER BY coins DESC LIMIT ?", (limit,))
        return [dict(r) for r in c.fetchall()]

    def get_referrals(self, user_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE referrer_id = ?", (user_id,))
        return [dict(r) for r in c.fetchall()]

    def get_all_users(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM users ORDER BY coins DESC")
        return [dict(r) for r in c.fetchall()]

    def get_user_count(self) -> int:
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        return c.fetchone()[0]

    # ── Levels ────────────────────────────────────────
    def get_user_level(self, coins: int) -> int:
        c = self.conn.cursor()
        c.execute("SELECT level FROM level_thresholds WHERE min_coins <= ? ORDER BY min_coins DESC LIMIT 1", (coins,))
        row = c.fetchone()
        return row[0] if row else 1

    def get_next_level_coins(self, current_level: int) -> int:
        c = self.conn.cursor()
        c.execute("SELECT min_coins FROM level_thresholds WHERE level = ?", (current_level + 1,))
        row = c.fetchone()
        return row[0] if row else 0

    # ── Character Images ──────────────────────────────
    def get_character_image(self, key: str) -> Optional[str]:
        c = self.conn.cursor()
        c.execute("SELECT file_id FROM character_images WHERE key = ?", (key,))
        row = c.fetchone()
        return row[0] if row else None

    def set_character_image(self, key: str, file_id: str):
        self.conn.execute("INSERT OR REPLACE INTO character_images (key, file_id) VALUES (?, ?)", (key, file_id))
        self.conn.commit()

    def get_all_character_images(self) -> Dict:
        c = self.conn.cursor()
        c.execute("SELECT key, file_id FROM character_images")
        return {r["key"]: r["file_id"] for r in c.fetchall()}

    # ── Categories ────────────────────────────────────
    def get_categories(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM categories ORDER BY sort_order, id")
        return [dict(r) for r in c.fetchall()]

    def create_category(self, name: str, icon: str) -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
        self.conn.commit()
        return c.lastrowid

    def update_category(self, cat_id: int, name: str, icon: str):
        self.conn.execute("UPDATE categories SET name=?, icon=? WHERE id=?", (name, icon, cat_id))
        self.conn.commit()

    def delete_category(self, cat_id: int):
        self.conn.execute("DELETE FROM cards WHERE category_id=?", (cat_id,))
        self.conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
        self.conn.commit()

    # ── Cards ─────────────────────────────────────────
    def get_cards_by_category(self, cat_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM cards WHERE category_id=?", (cat_id,))
        return [dict(r) for r in c.fetchall()]

    def get_all_cards(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT c.*, cat.name as cat_name FROM cards c LEFT JOIN categories cat ON c.category_id=cat.id")
        return [dict(r) for r in c.fetchall()]

    def get_card(self, card_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM cards WHERE id=?", (card_id,))
        row = c.fetchone()
        return dict(row) if row else None

    def create_card(self, cat_id: int, name: str, base_profit: int, base_cost: int) -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO cards (category_id, name, base_profit, base_cost) VALUES (?,?,?,?)",
                  (cat_id, name, base_profit, base_cost))
        self.conn.commit()
        return c.lastrowid

    def update_card(self, card_id: int, name: str, base_profit: int, base_cost: int, cat_id: int):
        self.conn.execute(
            "UPDATE cards SET name=?, base_profit=?, base_cost=?, category_id=? WHERE id=?",
            (name, base_profit, base_cost, cat_id, card_id)
        )
        self.conn.commit()

    def delete_card(self, card_id: int):
        self.conn.execute("DELETE FROM user_cards WHERE card_id=?", (card_id,))
        self.conn.execute("DELETE FROM card_images WHERE card_id=?", (card_id,))
        self.conn.execute("DELETE FROM cards WHERE id=?", (card_id,))
        self.conn.commit()

    def get_card_image(self, card_id: int, level: int) -> Optional[str]:
        c = self.conn.cursor()
        # اول دنبال سطح خاص بگرد، اگر نبود سطح ۱ را برگردان
        c.execute("SELECT file_id FROM card_images WHERE card_id=? AND level=?", (card_id, level))
        row = c.fetchone()
        if row:
            return row[0]
        c.execute("SELECT file_id FROM card_images WHERE card_id=? ORDER BY level LIMIT 1", (card_id,))
        row = c.fetchone()
        return row[0] if row else None

    def set_card_image(self, card_id: int, level: int, file_id: str):
        self.conn.execute("INSERT OR REPLACE INTO card_images (card_id, level, file_id) VALUES (?,?,?)",
                          (card_id, level, file_id))
        self.conn.commit()

    # ── User Cards ────────────────────────────────────
    def get_user_cards(self, user_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM user_cards WHERE user_id=?", (user_id,))
        return [dict(r) for r in c.fetchall()]

    def get_user_card(self, user_id: int, card_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM user_cards WHERE user_id=? AND card_id=?", (user_id, card_id))
        row = c.fetchone()
        return dict(row) if row else None

    def upgrade_user_card(self, user_id: int, card_id: int):
        existing = self.get_user_card(user_id, card_id)
        if existing:
            self.conn.execute(
                "UPDATE user_cards SET level = MIN(10, level + 1) WHERE user_id=? AND card_id=?",
                (user_id, card_id)
            )
        else:
            self.conn.execute(
                "INSERT INTO user_cards (user_id, card_id, level) VALUES (?,?,1)",
                (user_id, card_id)
            )
        self.conn.commit()

    def get_user_profit_per_hour(self, user_id: int) -> int:
        c = self.conn.cursor()
        c.execute("""
            SELECT SUM(ca.base_profit * uc.level) as total
            FROM user_cards uc
            JOIN cards ca ON uc.card_id = ca.id
            WHERE uc.user_id = ?
        """, (user_id,))
        row = c.fetchone()
        return int(row[0] or 0)

    def get_coins_per_tap(self, user_id: int) -> int:
        settings = self.get_settings()
        return int(settings.get("coins_per_tap", 1))

    # ── Admin stats ───────────────────────────────────
    def get_total_coins(self) -> int:
        c = self.conn.cursor()
        c.execute("SELECT SUM(coins) FROM users")
        row = c.fetchone()
        return int(row[0] or 0)
