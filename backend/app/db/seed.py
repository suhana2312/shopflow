from decimal import Decimal
from app.core.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.core.security import get_password_hash
from app.core.logging import logger

def seed_database():
    db = SessionLocal()
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)

        # 1. Seed Users
        admin = db.query(User).filter(User.email == "admin@shopflow.io").first()
        if not admin:
            admin = User(
                email="admin@shopflow.io",
                hashed_password=get_password_hash("AdminSecret123!"),
                full_name="Platform Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)

        customer1 = db.query(User).filter(User.email == "customer@shopflow.io").first()
        if not customer1:
            customer1 = User(
                email="customer@shopflow.io",
                hashed_password=get_password_hash("CustomerPass123!"),
                full_name="Alex Johnson",
                role=UserRole.CUSTOMER,
                is_active=True
            )
            db.add(customer1)

        customer2 = db.query(User).filter(User.email == "customer2@shopflow.io").first()
        if not customer2:
            customer2 = User(
                email="customer2@shopflow.io",
                hashed_password=get_password_hash("CustomerPass123!"),
                full_name="Sarah Miller",
                role=UserRole.CUSTOMER,
                is_active=True
            )
            db.add(customer2)

        db.commit()

        # 2. Seed Categories
        categories_data = [
            {"name": "Laptops & Computers", "slug": "laptops-computers", "description": "High-performance laptops, ultrabooks, and workstations"},
            {"name": "Audio & Sound", "slug": "audio-sound", "description": "Premium noise-cancelling headphones, earbuds, and speakers"},
            {"name": "Keyboards & Mice", "slug": "keyboards-mice", "description": "Mechanical keyboards, ergonomic mice, and desk pads"},
            {"name": "Displays & Monitors", "slug": "displays-monitors", "description": "Color-accurate 4K/UHD and high-refresh-rate displays"},
            {"name": "Accessories & Docks", "slug": "accessories-docks", "description": "Thunderbolt docks, ergonomic stands, and streaming gear"}
        ]

        category_map = {}
        for cat_info in categories_data:
            cat = db.query(Category).filter(Category.slug == cat_info["slug"]).first()
            if not cat:
                cat = Category(
                    name=cat_info["name"],
                    slug=cat_info["slug"],
                    description=cat_info["description"],
                    is_active=True
                )
                db.add(cat)
                db.flush()
            category_map[cat.slug] = cat.id

        db.commit()

        # 3. Seed Products & Inventory
        products_data = [
            {
                "sku": "LAP-PRO-15",
                "name": "UltraBook Pro 15.6\"",
                "description": "3.2GHz 16-Core processor, 32GB RAM, 1TB NVMe SSD, OLED 120Hz display with aluminum chassis.",
                "price": Decimal("1299.99"),
                "discount_price": Decimal("1199.99"),
                "category_slug": "laptops-computers",
                "brand": "AeroTech",
                "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80",
                "stock": 25,
                "low_stock_threshold": 5
            },
            {
                "sku": "DESK-APEX-X",
                "name": "Gaming Rig Apex X",
                "description": "Liquid-cooled gaming desktop with RTX 4080, 64GB DDR5, PCIe 5.0 storage, tempered glass case.",
                "price": Decimal("1899.99"),
                "discount_price": None,
                "category_slug": "laptops-computers",
                "brand": "ApexForce",
                "image_url": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=800&q=80",
                "stock": 10,
                "low_stock_threshold": 3
            },
            {
                "sku": "KB-MECH-01",
                "name": "Custom Mechanical Keyboard 75%",
                "description": "Hot-swappable linear switches, PBT double-shot keycaps, RGB backlighting, gasket mounted.",
                "price": Decimal("129.99"),
                "discount_price": Decimal("109.99"),
                "category_slug": "keyboards-mice",
                "brand": "KeyCraft",
                "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=800&q=80",
                "stock": 50,
                "low_stock_threshold": 10
            },
            {
                "sku": "MSE-ERGO-02",
                "name": "Ergonomic Precision Wireless Mouse",
                "description": "Dual Bluetooth and 2.4GHz connectivity, 8K DPI sensor, infinite hyper-scroll wheel, 70-day battery.",
                "price": Decimal("69.99"),
                "discount_price": None,
                "category_slug": "keyboards-mice",
                "brand": "KeyCraft",
                "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=800&q=80",
                "stock": 40,
                "low_stock_threshold": 8
            },
            {
                "sku": "MON-4K-27",
                "name": "StudioVision 27\" 4K HDR Monitor",
                "description": "99% DCI-P3 color gamut, 400 nits brightness, USB-C 90W Power Delivery, height-adjustable stand.",
                "price": Decimal("499.99"),
                "discount_price": Decimal("459.99"),
                "category_slug": "displays-monitors",
                "brand": "ViewMaster",
                "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80",
                "stock": 15,
                "low_stock_threshold": 5
            },
            {
                "sku": "AUD-ANC-PRO",
                "name": "SonicAir Pro Wireless ANC Headphones",
                "description": "Hybrid Active Noise Cancellation, 40mm beryllium drivers, Spatial Audio, 45-hour battery life.",
                "price": Decimal("199.99"),
                "discount_price": Decimal("179.99"),
                "category_slug": "audio-sound",
                "brand": "SonicAir",
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
                "stock": 30,
                "low_stock_threshold": 10
            },
            {
                "sku": "ACC-STAND-01",
                "name": "Precision Aluminum Laptop Stand",
                "description": "CNC machined aerospace aluminum, ergonomic viewing angle, heat dissipation ventilation cutout.",
                "price": Decimal("49.99"),
                "discount_price": None,
                "category_slug": "accessories-docks",
                "brand": "DeskPro",
                "image_url": "https://images.unsplash.com/photo-1616353071855-2c045c4458ae?auto=format&fit=crop&w=800&q=80",
                "stock": 60,
                "low_stock_threshold": 15
            },
            {
                "sku": "ACC-DOCK-10",
                "name": "10-in-1 Thunderbolt 4 Docking Station",
                "description": "Dual 4K@60Hz display support, 100W PD charging, 2.5G Gigabit Ethernet, SD card reader, 4x USB 3.2.",
                "price": Decimal("179.99"),
                "discount_price": Decimal("159.99"),
                "category_slug": "accessories-docks",
                "brand": "DeskPro",
                "image_url": "https://images.unsplash.com/photo-1544652478-6653e09f18a2?auto=format&fit=crop&w=800&q=80",
                "stock": 20,
                "low_stock_threshold": 5
            },
            {
                "sku": "CAM-4K-PRO",
                "name": "StreamClear 4K Pro Webcam",
                "description": "Sony STARVIS CMOS sensor, dual omnidirectional noise-cancelling mics, HDR auto light correction.",
                "price": Decimal("139.99"),
                "discount_price": None,
                "category_slug": "accessories-docks",
                "brand": "StreamClear",
                "image_url": "https://images.unsplash.com/photo-1588508065123-287b28e013da?auto=format&fit=crop&w=800&q=80",
                "stock": 25,
                "low_stock_threshold": 5
            },
            {
                "sku": "FLASH-PROMO-01",
                "name": "Limited Edition Mechanical Switch Tester (Stock = 1)",
                "description": "Exclusive collectible 9-key switch tester with novelty keycaps. Flash sale item with exactly 1 unit in stock!",
                "price": Decimal("29.99"),
                "discount_price": None,
                "category_slug": "keyboards-mice",
                "brand": "KeyCraft",
                "image_url": "https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=800&q=80",
                "stock": 1,
                "low_stock_threshold": 2
            }
        ]

        for p_info in products_data:
            existing_prod = db.query(Product).filter(Product.sku == p_info["sku"]).first()
            if not existing_prod:
                prod = Product(
                    sku=p_info["sku"],
                    name=p_info["name"],
                    description=p_info["description"],
                    price=p_info["price"],
                    discount_price=p_info["discount_price"],
                    category_id=category_map.get(p_info["category_slug"]),
                    brand=p_info["brand"],
                    image_url=p_info["image_url"],
                    is_active=True
                )
                db.add(prod)
                db.flush()

                # Add inventory
                inv = Inventory(
                    product_id=prod.id,
                    available_quantity=p_info["stock"],
                    reserved_quantity=0,
                    sold_quantity=0,
                    low_stock_threshold=p_info["low_stock_threshold"]
                )
                db.add(inv)

        db.commit()
        print("Database seeded successfully with demo users, categories, products, and inventory!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
