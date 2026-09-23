from decimal import Decimal
from app.models.inventory import Inventory
from app.models.outbox import OutboxEvent

def test_checkout_order_creation_and_reservation(client, customer_token, sample_product, db_session):
    # 1. Add item to cart
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 2},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # 2. Checkout
    checkout_payload = {
        "shipping_address": {
            "full_name": "Alex Johnson",
            "street": "123 Tech Boulevard",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94107",
            "country": "United States",
            "phone": "+14155552671"
        },
        "payment_method": "SIMULATED_CARD"
    }

    checkout_resp = client.post(
        "/api/v1/checkout",
        json=checkout_payload,
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert checkout_resp.status_code == 201
    order_data = checkout_resp.json()["data"]

    assert order_data["status"] == "PAYMENT_PENDING"
    assert order_data["order_number"].startswith("ORD-")
    assert len(order_data["items"]) == 1

    # 3. Assert Inventory Reservation
    inv = db_session.query(Inventory).filter(Inventory.product_id == sample_product.id).first()
    assert inv.available_quantity == 8  # 10 - 2 = 8
    assert inv.reserved_quantity == 2

    # 4. Assert Outbox Event Created
    outbox = db_session.query(OutboxEvent).filter(
        OutboxEvent.aggregate_id == order_data["id"],
        OutboxEvent.event_type == "OrderCreated"
    ).first()
    assert outbox is not None

def test_admin_update_order_status_lifecycle(client, customer_token, admin_token, sample_product):
    # 1. Create order
    client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 1},
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

    # 2. Simulate Payment to move order to CONFIRMED
    client.post(
        f"/api/v1/orders/{order_id}/simulate-payment",
        json={"outcome": "SUCCESS"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # 3. Admin updates CONFIRMED -> PROCESSING (Valid)
    resp = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "PROCESSING"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PROCESSING"

    # 4. Admin tries invalid transition: PROCESSING -> DELIVERED (Invalid! Must go PACKED -> SHIPPED -> OUT_FOR_DELIVERY -> DELIVERED)
    invalid_resp = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "DELIVERED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert invalid_resp.status_code == 409
    assert invalid_resp.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
