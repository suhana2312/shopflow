import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory

import os

TEST_DB_FILE = "./test_shopflow.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False, "timeout": 30.0}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
    Base.metadata.create_all(bind=test_engine)
    yield
    test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_admin_user(db_session):
    existing = db_session.query(User).filter(User.email == "test_admin@shopflow.io").first()
    if existing:
        return existing
    user = User(
        email="test_admin@shopflow.io",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_customer_user(db_session):
    existing = db_session.query(User).filter(User.email == "test_customer@shopflow.io").first()
    if existing:
        return existing
    user = User(
        email="test_customer@shopflow.io",
        hashed_password=get_password_hash("CustomerPass123!"),
        full_name="Test Customer",
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_customer_user_2(db_session):
    existing = db_session.query(User).filter(User.email == "test_customer_2@shopflow.io").first()
    if existing:
        return existing
    user = User(
        email="test_customer_2@shopflow.io",
        hashed_password=get_password_hash("CustomerPass123!"),
        full_name="Second Customer",
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_token(test_admin_user):
    return create_access_token(subject=test_admin_user.id, role=test_admin_user.role.value)

@pytest.fixture
def customer_token(test_customer_user):
    return create_access_token(subject=test_customer_user.id, role=test_customer_user.role.value)

@pytest.fixture
def customer_token_2(test_customer_user_2):
    return create_access_token(subject=test_customer_user_2.id, role=test_customer_user_2.role.value)

@pytest.fixture
def sample_category(db_session):
    existing = db_session.query(Category).filter(Category.slug == "electronics").first()
    if existing:
        return existing
    cat = Category(
        name="Electronics",
        slug="electronics",
        description="Consumer electronics",
        is_active=True
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat

@pytest.fixture
def sample_product(db_session, sample_category):
    existing = db_session.query(Product).filter(Product.sku == "TEST-SKU-001").first()
    if existing:
        existing.is_active = True
        inv = db_session.query(Inventory).filter(Inventory.product_id == existing.id).first()
        if inv:
            inv.available_quantity = 10
            inv.reserved_quantity = 0
            inv.sold_quantity = 0
        db_session.commit()
        return existing

    prod = Product(
        sku="TEST-SKU-001",
        name="Wireless Ergonomic Keyboard",
        description="High-grade keyboard",
        price=Decimal("99.99"),
        discount_price=Decimal("89.99"),
        category_id=sample_category.id,
        brand="KeyCraft",
        is_active=True
    )
    db_session.add(prod)
    db_session.flush()

    inv = Inventory(
        product_id=prod.id,
        available_quantity=10,
        reserved_quantity=0,
        sold_quantity=0,
        low_stock_threshold=2
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(prod)
    return prod

@pytest.fixture
def single_stock_product(db_session, sample_category):
    """Product with exactly 1 unit in stock for critical concurrency tests."""
    existing = db_session.query(Product).filter(Product.sku == "FLASH-CONCURRENCY-01").first()
    if existing:
        inv = db_session.query(Inventory).filter(Inventory.product_id == existing.id).first()
        if inv:
            inv.available_quantity = 1
            inv.reserved_quantity = 0
            inv.sold_quantity = 0
            db_session.commit()
        return existing

    prod = Product(
        sku="FLASH-CONCURRENCY-01",
        name="Sole Remaining Flash Product",
        description="Last remaining item",
        price=Decimal("49.99"),
        category_id=sample_category.id,
        brand="RareBrand",
        is_active=True
    )
    db_session.add(prod)
    db_session.flush()

    inv = Inventory(
        product_id=prod.id,
        available_quantity=1,
        reserved_quantity=0,
        sold_quantity=0,
        low_stock_threshold=1
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(prod)
    return prod
