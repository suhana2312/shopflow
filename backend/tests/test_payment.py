from app.models.inventory import Inventory

def test_payment_success_transitions(client, customer_token, sample_product, db_session):
    # 1. Place order for 2 items
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 2},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    checkout_resp = client.post(
        "/api/v1/checkout",
        json={
            "shipping_address": {
                "full_name": "Alex Johnson",
                "street": "123 Tech Boulevard",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94107",
                "phone": "+14155552671"
            }
        },
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    order_id = checkout_resp.json()["data"]["id"]

    # 2. Simulate Payment SUCCESS
    pay_resp = client.post(
        f"/api/v1/orders/{order_id}/simulate-payment",
        json={"outcome": "SUCCESS"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["data"]["status"] == "SUCCESS"

    # 3. Verify Inventory: RESERVED -> SOLD
    inv = db_session.query(Inventory).filter(Inventory.product_id == sample_product.id).first()
    assert inv.available_quantity == 8
    assert inv.reserved_quantity == 0
    assert inv.sold_quantity == 2

    # 4. Test Payment Idempotency: Calling payment endpoint again returns existing payment
    second_pay_resp = client.post(
        f"/api/v1/orders/{order_id}/simulate-payment",
        json={"outcome": "SUCCESS"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert second_pay_resp.status_code == 200
    assert second_pay_resp.json()["data"]["id"] == pay_resp.json()["data"]["id"]

    # Inventory must remain exactly the same
    assert inv.sold_quantity == 2

def test_payment_failure_releases_inventory(client, customer_token, sample_product, db_session):
    # 1. Place order for 2 items
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 2},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    checkout_resp = client.post(
        "/api/v1/checkout",
        json={
            "shipping_address": {
                "full_name": "Alex Johnson",
                "street": "123 Tech Boulevard",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94107",
                "phone": "+14155552671"
            }
        },
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    order_id = checkout_resp.json()["data"]["id"]

    # 2. Simulate Payment FAILED
    pay_resp = client.post(
        f"/api/v1/orders/{order_id}/simulate-payment",
        json={"outcome": "FAILED"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["data"]["status"] == "FAILED"

    # 3. Verify Inventory: RESERVED -> AVAILABLE
    inv = db_session.query(Inventory).filter(Inventory.product_id == sample_product.id).first()
    assert inv.available_quantity == 10  # Restored!
    assert inv.reserved_quantity == 0
    assert inv.sold_quantity == 0
