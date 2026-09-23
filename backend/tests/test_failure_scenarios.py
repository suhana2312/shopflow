def test_scenario_product_not_found(client):
    resp = client.get("/api/v1/products/non-existent-uuid-12345")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

def test_scenario_add_inactive_product_to_cart(client, customer_token, sample_product, db_session):
    sample_product.is_active = False
    db_session.commit()

    resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"

    sample_product.is_active = True
    db_session.commit()

def test_scenario_insufficient_stock(client, customer_token, sample_product):
    sample_product.is_active = True
    # Request 50 units when stock is only 10
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 50},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    resp = client.post(
        "/api/v1/checkout",
        json={
            "shipping_address": {
                "full_name": "Test User",
                "street": "123 St",
                "city": "City",
                "state": "ST",
                "postal_code": "12345",
                "phone": "+1234567890"
            }
        },
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "OUT_OF_STOCK"

def test_scenario_duplicate_checkout_idempotency(client, customer_token, sample_product):
    client.delete("/api/v1/cart", headers={"Authorization": f"Bearer {customer_token}"})
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    idempotency_key = "idemp-test-unique-key-999"
    payload = {
        "shipping_address": {
            "full_name": "Idempotent Buyer",
            "street": "123 St",
            "city": "City",
            "state": "ST",
            "postal_code": "12345",
            "phone": "+1234567890"
        }
    }

    # Request 1
    resp1 = client.post(
        "/api/v1/checkout",
        json=payload,
        headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": idempotency_key}
    )
    assert resp1.status_code == 201
    order_id_1 = resp1.json()["data"]["id"]

    # Request 2 with identical key
    resp2 = client.post(
        "/api/v1/checkout",
        json=payload,
        headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": idempotency_key}
    )
    assert resp2.status_code == 201
    order_id_2 = resp2.json()["data"]["id"]

    # Must return existing order without creating duplicate!
    assert order_id_1 == order_id_2

def test_scenario_unauthorized_order_access(client, customer_token, customer_token_2, sample_product):
    # Customer 1 creates order
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    checkout_resp = client.post(
        "/api/v1/checkout",
        json={
            "shipping_address": {
                "full_name": "Customer 1",
                "street": "123 St",
                "city": "City",
                "state": "ST",
                "postal_code": "12345",
                "phone": "+1234567890"
            }
        },
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    order_id = checkout_resp.json()["data"]["id"]

    # Customer 2 attempts to view Customer 1's order -> 403 Forbidden
    cross_access_resp = client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {customer_token_2}"}
    )
    assert cross_access_resp.status_code == 403
    assert cross_access_resp.json()["error"]["code"] == "UNAUTHORIZED_ORDER_ACCESS"
