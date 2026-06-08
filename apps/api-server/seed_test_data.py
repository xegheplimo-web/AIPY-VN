"""
Seed database with test data for VietStore RAG
"""

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from src.database import async_session
from src.models.user import User, Address
from src.models.store import Store, Product, Category
from src.models.order import Order, OrderItem
from src.models.promotion import Promotion
from src.models.report import Report
from src.api.auth import hash_password


async def seed_categories():
    """Seed categories"""
    categories_data = [
        {"name": "Thực phẩm", "slug": "thuc-pham", "sort_order": 1},
        {"name": "Đồ uống", "slug": "do-uong", "sort_order": 2},
        {"name": "Đồ gia dụng", "slug": "do-gia-dung", "sort_order": 3},
        {"name": "Thời trang", "slug": "thoi-trang", "sort_order": 4},
        {"name": "Điện tử", "slug": "dien-tu", "sort_order": 5},
        {"name": "Sức khỏe", "slug": "suc-khoe", "sort_order": 6},
    ]

    async with async_session() as session:
        for cat_data in categories_data:
            existing = await session.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )
            if not existing.scalar_one_or_none():
                category = Category(**cat_data)
                session.add(category)
        await session.commit()
        print("✓ Categories seeded")


async def seed_users():
    """Seed test users"""
    password_hash = hash_password("Password123")
    users_data = [
        {
            "email": "customer@example.com",
            "password_hash": password_hash,
            "full_name": "Nguyễn Văn A",
            "phone": "0901234567",
            "role": "customer",
        },
        {
            "email": "owner@example.com",
            "password_hash": password_hash,
            "full_name": "Trần Thị B",
            "phone": "0909876543",
            "role": "owner",
        },
        {
            "email": "admin@example.com",
            "password_hash": password_hash,
            "full_name": "Admin User",
            "phone": "0905555555",
            "role": "admin",
        },
    ]

    async with async_session() as session:
        for user_data in users_data:
            existing = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            if not existing.scalar_one_or_none():
                user = User(**user_data)
                session.add(user)
        await session.commit()
        print("✓ Users seeded")


async def seed_stores():
    """Seed test stores"""
    stores_data = [
        {
            "name": "Cửa hàng Tạp hóa A",
            "address": "123 Đường ABC, Quận 1, TP.HCM",
            "latitude": 10.7769,
            "longitude": 106.7009,
            "phone": "0901234567",
            "email": "store1@example.com",
            "industry": "Thực phẩm",
            "status": "active",
        },
        {
            "name": "Siêu thị Mini B",
            "address": "456 Đường XYZ, Quận 3, TP.HCM",
            "latitude": 10.7850,
            "longitude": 106.6900,
            "phone": "0902345678",
            "email": "store2@example.com",
            "industry": "Đồ gia dụng",
            "status": "active",
        },
        {
            "name": "Cửa hàng Điện tử C",
            "address": "789 Đường DEF, Quận 5, TP.HCM",
            "latitude": 10.7600,
            "longitude": 106.6800,
            "phone": "0903456789",
            "email": "store3@example.com",
            "industry": "Điện tử",
            "status": "active",
        },
    ]

    async with async_session() as session:
        for store_data in stores_data:
            existing = await session.execute(
                select(Store).where(Store.name == store_data["name"])
            )
            if not existing.scalar_one_or_none():
                store = Store(**store_data)
                session.add(store)
        await session.commit()
        print("✓ Stores seeded")


async def seed_products():
    """Seed test products"""
    async with async_session() as session:
        # Get stores
        stores_result = await session.execute(select(Store))
        stores = stores_result.scalars().all()

        # Get categories
        categories_result = await session.execute(select(Category))
        categories = categories_result.scalars().all()

        if not stores or not categories:
            print("⚠ No stores or categories found, skipping products")
            return

        products_data = [
            {
                "store_id": stores[0].id,
                "name": "Gạo ST25",
                "description": "Gạo ST25 ngon, thơm",
                "price": 150000,
                "stock": 100,
                "unit": "kg",
                "category_id": categories[0].id,
            },
            {
                "store_id": stores[0].id,
                "name": "Nước mắm Nam Ngư",
                "description": "Nước mắm ngon",
                "price": 45000,
                "stock": 50,
                "unit": "chai",
                "category_id": categories[0].id,
            },
            {
                "store_id": stores[1].id,
                "name": "Bình giữ nhiệt",
                "description": "Bình giữ nhiệt 500ml",
                "price": 250000,
                "stock": 30,
                "unit": "cái",
                "category_id": categories[2].id,
            },
            {
                "store_id": stores[2].id,
                "name": "Tai nghe Bluetooth",
                "description": "Tai nghe không dây",
                "price": 350000,
                "stock": 20,
                "unit": "cái",
                "category_id": categories[4].id,
            },
        ]

        for product_data in products_data:
            existing = await session.execute(
                select(Product).where(
                    Product.name == product_data["name"],
                    Product.store_id == product_data["store_id"],
                )
            )
            if not existing.scalar_one_or_none():
                product = Product(**product_data)
                session.add(product)
        await session.commit()
        print("✓ Products seeded")


async def seed_promotions():
    """Seed test promotions"""
    promotions_data = [
        {
            "code": "GIAM10",
            "name": "Giảm 10% toàn bộ",
            "type": "percentage",
            "value": 10,
            "min_order_amount": 100000,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "status": "active",
            "applicable_stores": ["all"],
        },
        {
            "code": "FREESHIP",
            "name": "Miễn phí ship",
            "type": "free_shipping",
            "value": 0,
            "min_order_amount": 200000,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "status": "active",
            "applicable_stores": ["all"],
        },
    ]

    async with async_session() as session:
        for promo_data in promotions_data:
            existing = await session.execute(
                select(Promotion).where(Promotion.code == promo_data["code"])
            )
            if not existing.scalar_one_or_none():
                promotion = Promotion(**promo_data)
                session.add(promotion)
        await session.commit()
        print("✓ Promotions seeded")


async def seed_reports():
    """Seed test reports"""
    async with async_session() as session:
        # Get users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()

        if not users:
            print("⚠ No users found, skipping reports")
            return

        reports_data = [
            {
                "type": "store",
                "target_id": users[1].id,  # Owner user
                "target_name": "Cửa hàng Tạp hóa A",
                "reporter_id": users[0].id,  # Customer user
                "reporter_name": users[0].full_name,
                "reason": "fake_products",
                "description": "Sản phẩm không đúng mô tả",
                "status": "pending",
            },
        ]

        for report_data in reports_data:
            existing = await session.execute(
                select(Report).where(
                    Report.target_id == report_data["target_id"],
                    Report.reporter_id == report_data["reporter_id"],
                )
            )
            if not existing.scalar_one_or_none():
                report = Report(**report_data)
                session.add(report)
        await session.commit()
        print("✓ Reports seeded")


async def main():
    """Run all seed functions"""
    print("🌱 Seeding database...")
    await seed_categories()
    await seed_users()
    await seed_stores()
    await seed_products()
    await seed_promotions()
    await seed_reports()
    print("✅ Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
