import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from src.config import config

logger = logging.getLogger(__name__)

engine = create_async_engine(config.database.url)


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM stores"))
        logger.info(f"Stores: {result.scalar()}")
        result2 = await conn.execute(text("SELECT COUNT(*) FROM products"))
        logger.info(f"Products: {result2.scalar()}")
        result3 = await conn.execute(text("SELECT COUNT(*) FROM categories"))
        logger.info(f"Categories: {result3.scalar()}")
        result4 = await conn.execute(
            text("SELECT name, latitude, longitude FROM stores LIMIT 3")
        )
        for row in result4:
            logger.info(f"  - {row[0]}: ({row[1]}, {row[2]})")


asyncio.run(check())
