import aiosqlite
from config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                budget_category TEXT,
                price TEXT,
                description TEXT,
                photos TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                phone TEXT,
                address TEXT,
                delivery_date TEXT,
                product_id INTEGER,
                status TEXT DEFAULT 'new'
            )
        ''')

        cursor = await db.execute("SELECT COUNT(*) FROM products")
        if (await cursor.fetchone())[0] == 0:
            sample_products = [
                ("Весенний сад", "garden", "3500-6500", "Прекрасный сад в вашем доме.", "FILE_ID_1"),
                ("Корзины и Кашпо", "baskets", "15000-20000", "Премиальные композиции.", "FILE_ID_1"),
                ("Ведра", "buckets", "3500", "Стильное оформление в ведрах.", "FILE_ID_1"),
                ("Ведерки и корзинки", "small_baskets", "1500-3500", "Уютные небольшие подарки.", "FILE_ID_1"),
                ("Тюльпаны", "tulips", "200", "Цена за одну штуку.", "FILE_ID_1"),
                ("25 шт", "tulip_wraps", "5500", "Сверток тюльпанов.", "FILE_ID_1"),
                ("35 шт", "tulip_wraps", "7500", "Сверток тюльпанов.", "FILE_ID_1"),
                ("50 шт", "tulip_wraps", "10500", "Сверток тюльпанов.", "FILE_ID_1"),
                ("15 шт", "roses", "3500", "Сибирские розы.", "FILE_ID_1"),
                ("101 шт", "roses", "25000", "Огромный букет сибирских роз.", "FILE_ID_1"),
                ("Весенние букеты", "spring_bouquets", "3500-5000", "Сезонные цветы.", "FILE_ID_1"),
            ]
            await db.executemany(
                "INSERT INTO products (name, budget_category, price, description, photos) VALUES (?, ?, ?, ?, ?)",
                sample_products,
            )
        await db.commit()


async def get_product_by_category(category: str, offset: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, name, price, description, photos FROM products WHERE budget_category = ? LIMIT 1 OFFSET ?",
            (category, offset),
        )
        return await cursor.fetchone()


async def count_products_by_category(category: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM products WHERE budget_category = ?", (category,)
        )
        res = await cursor.fetchone()
        return res[0] if res else 0


async def create_order(
    user_id: int, user_name: str, phone: str, address: str, date: str, product_id: int
):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, user_name, phone, address, delivery_date, product_id) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, user_name, phone, address, date, product_id),
        )
        await db.commit()
        return cursor.lastrowid


async def get_product_name(product_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT name, budget_category FROM products WHERE id = ?", (product_id,)
        )
        result = await cursor.fetchone()
        if result:
            name, cat = result
            cat_map = {
                "garden": "Весенний сад",
                "baskets": "Корзины и Кашпо",
                "buckets": "Ведра",
                "small_baskets": "Ведерки и корзинки",
                "tulips": "Тюльпаны",
                "spring_bouquets": "Весенние букеты",
            }
            return cat_map.get(cat, name)
        return "Неизвестный товар"


async def mark_order_completed(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,)
        )
        await db.commit()
