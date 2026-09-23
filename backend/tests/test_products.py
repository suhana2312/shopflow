from decimal import Decimal

def test_list_products_and_filter(client, sample_product):
    # Public listing
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] >= 1
    assert data["page"] == 1
    assert any(p["sku"] == sample_product.sku for p in data["items"])

    # Search filter
    resp_search = client.get(f"/api/v1/products?search={sample_product.name[:5]}")
    assert resp_search.status_code == 200
    search_data = resp_search.json()["data"]
    assert any(p["sku"] == sample_product.sku for p in search_data["items"])

    # Price range filter
    resp_price = client.get(f"/api/v1/products?min_price=50&max_price=150")
    assert resp_price.status_code == 200

def test_admin_create_product(client, admin_token, sample_category):
    payload = {
        "sku": "NEW-PROD-99",
        "name": "High Precision Stylus Pen",
        "description": "Pressure-sensitive digital stylus",
        "price": 79.99,
        "discount_price": 69.99,
        "category_id": sample_category.id,
        "brand": "DrawTech",
        "initial_stock": 20,
        "low_stock_threshold": 5
    }
    resp = client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["sku"] == "NEW-PROD-99"
    assert data["inventory"]["available_quantity"] == 20

def test_admin_create_duplicate_sku(client, admin_token, sample_product):
    payload = {
        "sku": sample_product.sku,
        "name": "Duplicate SKU Item",
        "price": 49.99,
        "initial_stock": 5
    }
    resp = client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "SKU_ALREADY_EXISTS"

def test_negative_price_rejected(client, admin_token):
    payload = {
        "sku": "NEG-PRICE-01",
        "name": "Negative Price Item",
        "price": -10.00,
        "initial_stock": 5
    }
    resp = client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 422  # Pydantic validation error
