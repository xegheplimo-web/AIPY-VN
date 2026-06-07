import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore")

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM stores"))
        print("Stores:", result.scalar())
        result2 = await conn.execute(text("SELECT COUNT(*) FROM products"))
        print("Products:", result2.scalar())
        result3 = await conn.execute(text("SELECT COUNT(*) FROM categories"))
        print("Categories:", result3.scalar())
        result4 = await conn.execute(text("SELECT name, latitude, longitude FROM stores LIMIT 3"))
        for row in result4:
            print(f"  - {row[0]}: ({row[1]}, {row[2]})")

asyncio.run(check())
