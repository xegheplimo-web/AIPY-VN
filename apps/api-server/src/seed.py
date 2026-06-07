import asyncio
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from models.store import Store, Product, Category
from models.user import User

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_data():
    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(select(Store))
        if result.scalars().first():
            print("Data already seeded. Skipping...")
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
                barcode="8935001234567",
                brand="GSK",
                shelf_location="Kệ A1, Tầng 1",
                category_id=cat_map["Thuốc & Dược phẩm"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Nhà thuốc An Khang - Nguyễn Trãi"],
                name="Vitamin C 1000mg",
                description="Tăng cường miễn dịch, chống oxy hóa",
                price=Decimal("85000"),
                stock=30,
                unit="lọ",
                weight_grams=80,
                barcode="8935001234568",
                brand="Kirkland",
                shelf_location="Kệ B2, Tầng 1",
                category_id=cat_map["Thực phẩm chức năng"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Nhà thuốc Long Châu - Lê Lợi"],
                name="Panadol Extra 500mg",
                description="Thuốc giảm đau, hạ sốt hiệu quả nhanh",
                price=Decimal("33000"),
                stock=12,
                unit="hộp",
                weight_grams=50,
                barcode="8935001234567",
                brand="GSK",
                shelf_location="Kệ A3, Tầng 1",
                category_id=cat_map["Thuốc & Dược phẩm"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Nhà thuốc Long Châu - Lê Lợi"],
                name="Khẩu trang y tế 4 lớp (hộp 50 cái)",
                description="Khẩu trang y tế chất lượng cao",
                price=Decimal("55000"),
                stock=200,
                unit="hộp",
                weight_grams=200,
                barcode="8935001234569",
                brand="VietMask",
                shelf_location="Kệ C1, Tầng 1",
                category_id=cat_map["Thiết bị y tế"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Pharmacity - Võ Văn Tần"],
                name="Omega-3 Fish Oil 1000mg",
                description="Bổ sung DHA, EPA tốt cho tim mạch và não bộ",
                price=Decimal("120000"),
                stock=25,
                unit="lọ",
                weight_grams=150,
                barcode="8935001234570",
                brand="Nature Made",
                shelf_location="Kệ D2, Tầng 1",
                category_id=cat_map["Thực phẩm chức năng"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Pharmacity - Võ Văn Tần"],
                name="Nước rửa tay khô On1 (500ml)",
                description="Sát khuẩn nhanh, không cần rửa lại",
                price=Decimal("45000"),
                stock=80,
                unit="chai",
                weight_grams=520,
                barcode="8935001234571",
                brand="On1",
                shelf_location="Kệ E1, Tầng 1",
                category_id=cat_map["Thiết bị y tế"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Guardian - Nguyễn Thị Minh Khai"],
                name="Kem dưỡng ẩm Cetaphil",
                description="Dưỡng ẩm nhẹ nhàng cho da nhạy cảm",
                price=Decimal("185000"),
                stock=15,
                unit="tuýp",
                weight_grams=150,
                barcode="8935001234572",
                brand="Cetaphil",
                shelf_location="Kệ F1, Tầng 1",
                category_id=cat_map["Mỹ phẩm"],
                status="active",
            ),
            Product(
                id=uuid.uuid4(),
                store_id=store_map["Co.opmart Cống Quỳnh"],
                name="Sữa tươi Vinamilk 1L",
                description="Sữa tươi tiệt trùng không đường",
                price=Decimal("28000"),
                stock=100,
                unit="hộp",
                weight_grams=1050,
                barcode="8935001234573",
                brand="Vinamilk",
                shelf_location="Kệ G3, Tầng 1",
                category_id=cat_map["Thực phẩm"],
                status="active",
            ),
        ]
        session.add_all(products)

        await session.commit()
        print(
            f"[OK] Seeded {len(categories)} categories, {len(stores)} stores, {len(products)} products"
        )


if __name__ == "__main__":
    asyncio.run(seed_data())
