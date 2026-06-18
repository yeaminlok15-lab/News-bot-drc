import aiosqlite
import logging
from src.config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # News Sources
        await db.execute('''CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT UNIQUE,
            category TEXT,
            language TEXT,
            is_active INTEGER DEFAULT 1
        )''')
        # Published News (Deduplication)
        await db.execute('''CREATE TABLE IF NOT EXISTS published_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Categories
        await db.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            is_active INTEGER DEFAULT 1
        )''')
        # Settings
        await db.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
        # Admins
        await db.execute('''CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )''')
        
        # Seed default categories
        default_cats = ['International', 'Bangladesh', 'Technology', 'Business', 'Sports']
        for cat in default_cats:
            await db.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))
            
        await db.commit()

async def is_published(url: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT 1 FROM published_news WHERE url = ?', (url,)) as cursor:
            return await cursor.fetchone() is not None

async def mark_published(url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT INTO published_news (url) VALUES (?)', (url,))
        await db.commit()

async def get_active_sources():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM sources WHERE is_active = 1') as cursor:
            return await cursor.fetchall()

async def add_source(name: str, url: str, category: str, language: str):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute('INSERT INTO sources (name, url, category, language) VALUES (?, ?, ?, ?)', 
                             (name, url, category, language))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False
