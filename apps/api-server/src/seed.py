# -*- coding: utf-8 -*-
import asyncio
import uuid
import sys
import os
import logging
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Ensure UTF-8 encoding for stdout/stderr
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.store import Store, Product, Category
from src.config import config

logger = logging.getLogger(__name__)

engine = create_async_engine(config.database.url)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_data():
    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(select(Store))
        if result.scalars().first():
            logger.info("Data already seeded. Skipping...")
            return

        # Categories
        categories = [
            Category(
                id=uuid.uuid4(),
                name="Thuốc & Dược phẩm",
                slug="thuoc-duoc-pham",
                description="Thuốc tân dược, thuốc đông y",
                sort_order=1,
            ),
            Category(
                id=uuid.uuid4(),
                name="Thực phẩm chức năng",
                slug="thuc-pham-chuc-nang",
                description="Vitamin, khoáng chất, collagen",
                sort_order=2,
            ),
            Category(
                id=uuid.uuid4(),
                name="Thiết bị y tế",
                slug="thiet-bi-y-te",
                description="Máy đo huyết áp, nhiệt kế, khẩu trang",
                sort_order=3,
            ),
            Category(
                id=uuid.uuid4(),
                name="Mỹ phẩm",
                slug="my-pham",
                description="Chăm sóc da, trang điểm",
                sort_order=4,
            ),
            Category(
                id=uuid.uuid4(),
                name="Thực phẩm",
                slug="thuc-pham",
                description="Đồ uống, snack, gia vị",
                sort_order=5,
            ),
        ]
        session.add_all(categories)
        await session.flush()

        cat_map = {c.name: c.id for c in categories}

        # Stores with real Vietnam coordinates (Ho Chi Minh City - District 1, 3, 5, 10)
        stores = [
            Store(
                id=uuid.uuid4(),
                name="Nhà thuốc An Khang - Nguyễn Trãi",
                address="123 Nguyễn Trãi, Phường Bến Thành, Quận 1, TP.HCM",
                latitude=10.7743,
                longitude=106.7009,
                phone="02838231234",
                email="ankhang.nguyentrai@example.com",
                zalo="0901234567",
                business_hours={
                    "monday": "07:00-22:00",
                    "tuesday": "07:00-22:00",
                    "wednesday": "07:00-22:00",
                    "thursday": "07:00-22:00",
                    "friday": "07:00-22:00",
                    "saturday": "07:00-22:00",
                    "sunday": "07:00-21:00",
                },
                is_open_now=True,
                rating=Decimal("4.5"),
                total_reviews=128,
                industry="Bán lẻ dược phẩm",
                status="active",
                location_verified=True,
            ),
            Store(
                id=uuid.uuid4(),
                name="Nhà thuốc Long Châu - Lê Lợi",
                address="456 Lê Lợi, Phường Bến Thành, Quận 1, TP.HCM",
                latitude=10.7751,
                longitude=106.7002,
                phone="02838234567",
                email="longchau.leloi@example.com",
                zalo="0902345678",
                business_hours={
                    "monday": "06:30-23:00",
                    "tuesday": "06:30-23:00",
                    "wednesday": "06:30-23:00",
                    "thursday": "06:30-23:00",
                    "friday": "06:30-23:00",
                    "saturday": "06:30-23:00",
                    "sunday": "06:30-22:00",
                },
                is_open_now=True,
                rating=Decimal("4.3"),
                total_reviews=256,
                industry="Bán lẻ dược phẩm",
                status="active",
                location_verified=True,
            ),
            Store(
                id=uuid.uuid4(),
                name="Pharmacity - Võ Văn Tần",
                address="789 Võ Văn Tần, Phường 6, Quận 3, TP.HCM",
                latitude=10.7795,
                longitude=106.6901,
                phone="02838237890",
                email="pharmacity.vvt@example.com",
                zalo="0903456789",
                business_hours={
                    "monday": "07:00-22:00",
                    "tuesday": "07:00-22:00",
                    "wednesday": "07:00-22:00",
                    "thursday": "07:00-22:00",
                    "friday": "07:00-22:00",
                    "saturday": "07:00-22:00",
                    "sunday": "08:00-21:00",
                },
                is_open_now=True,
                rating=Decimal("4.7"),
                total_reviews=512,
                industry="Bán lẻ dược phẩm",
                status="active",
                location_verified=True,
            ),
            Store(
                id=uuid.uuid4(),
                name="Guardian - Nguyễn Thị Minh Khai",
                address="101 Nguyễn Thị Minh Khai, Phường Bến Thành, Quận 1, TP.HCM",
                latitude=10.7721,
                longitude=106.6952,
                phone="02838231111",
                email="guardian.ntmk@example.com",
                zalo="0904567890",
                business_hours={
                    "monday": "09:00-22:00",
                    "tuesday": "09:00-22:00",
                    "wednesday": "09:00-22:00",
                    "thursday": "09:00-22:00",
                    "friday": "09:00-22:00",
                    "saturday": "09:00-22:00",
                    "sunday": "09:00-21:00",
                },
                is_open_now=True,
                rating=Decimal("4.2"),
                total_reviews=89,
                industry="Bán lẻ mỹ phẩm",
                status="active",
                location_verified=True,
            ),
            Store(
                id=uuid.uuid4(),
                name="Co.opmart Cống Quỳnh",
                address="189C Cống Quỳnh, Phường Nguyễn Thái Bình, Quận 1, TP.HCM",
                latitude=10.7674,
                longitude=106.6943,
                phone="02838239999",
                email="coopmart.cq@example.com",
                zalo="0905678901",
                business_hours={
                    "monday": "07:00-22:00",
                    "tuesday": "07:00-22:00",
                    "wednesday": "07:00-22:00",
                    "thursday": "07:00-22:00",
                    "friday": "07:00-22:00",
                    "saturday": "07:00-22:00",
                    "sunday": "07:00-22:00",
                },
                is_open_now=True,
                rating=Decimal("4.4"),
                total_reviews=342,
                industry="Siêu thị",
                status="active",
                location_verified=True,
            ),
        ]
        session.add_all(stores)
        await session.flush()

        store_map = {s.name: s.id for s in stores}

        # Products
        products = [
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Nhà thuốc An Khang - Nguyễn Trãi"],
                name="Panadol Extra 500mg",
                description="Thuốc giảm đau, hạ sốt hiệu quả nhanh",
                price=Decimal("35000"),
                stock=45,
                unit="hộp",
                weight_grams=50,
                barcode="8934567890123",
                shelf_location="A1-02",
                category_id=cat_map["Thuốc & Dược phẩm"],
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Nhà thuốc An Khang - Nguyễn Trãi"],
                name="Vitamin C 1000mg",
                description="Tăng cường đề kháng, chống oxy hóa",
                price=Decimal("85000"),
                stock=120,
                unit="lọ",
                weight_grams=100,
                barcode="8934567890124",
                shelf_location="A2-05",
                category_id=cat_map["Thực phẩm chức năng"],
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Nhà thuốc Long Châu - Lê Lợi"],
                name="Máy đo huyết áp Omron",
                description="Máy đo huyết áp điện tử chính xác",
                price=Decimal("650000"),
                stock=15,
                unit="cái",
                weight_grams=300,
                barcode="8934567890125",
                shelf_location="B1-01",
                category_id=cat_map["Thiết bị y tế"],
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Pharmacity - Võ Văn Tần"],
                name="Kem dưỡng da ban đêm",
                description="Dưỡng da trắng sáng, mờ thâm",
                price=Decimal("250000"),
                stock=80,
                unit="hũ",
                weight_grams=50,
                barcode="8934567890126",
                shelf_location="C3-10",
                category_id=cat_map["Mỹ phẩm"],
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Co.opmart Cống Quỳnh"],
                name="Sữa tươi Vinamilik 1L",
                description="Sữa tươi tiệt trùng bổ sung canxi",
                price=Decimal("32000"),
                stock=200,
                unit="hộp",
                weight_grams=1050,
                barcode="8934567890127",
                shelf_location="D1-15",
                category_id=cat_map["Thực phẩm"],
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]
        session.add_all(products)
        await session.commit()
        logger.info(
            f"Seeded {len(categories)} categories, {len(stores)} stores, {len(products)} products"
        )


if __name__ == "__main__":
    asyncio.run(seed_data())
