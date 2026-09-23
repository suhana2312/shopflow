import concurrent.futures
from app.models.inventory import Inventory

def test_critical_concurrent_checkout_prevents_overselling(
    client,
    customer_token,
    customer_token_2,
    single_stock_product,
    db_session
):
    """
    CRITICAL CONCURRENCY TEST (Prompt Section 15 & 60):
    Stock = 1.
    Customer 1 and Customer 2 simultaneously attempt to purchase the final unit.
    Expected:
      - Exactly 1 customer gets 201 Created (SUCCESS)
      - The other customer gets 409 Conflict (OUT_OF_STOCK)
      - Zero overselling: available_quantity >= 0, reserved_quantity <= 1
    """
    # 1. Customer 1 adds product (quantity = 1) to cart
    client.post(
        "/api/v1/cart/items",
        json={"product_id": single_stock_product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # 2. Customer 2 adds product (quantity = 1) to cart
    client.post(
        "/api/v1/cart/items",
        json={"product_id": single_stock_product.id, "quantity": 1},
        headers={"Authorization": f"Bearer {customer_token_2}"}
    )

    checkout_payload = {
        "shipping_address": {
            "full_name": "Concurrent Buyer",
            "street": "100 Market St",
            "city": "Austin",
            "state": "TX",
            "postal_code": "78701",
            "country": "United States",
            "phone": "+15125551234"
        }
    }

    results = []

    def perform_checkout(token):
        return client.post(
            "/api/v1/checkout",
            json=checkout_payload,
            headers={"Authorization": f"Bearer {token}"}
        )

    # Execute checkout concurrently across separate threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(perform_checkout, customer_token)
        future2 = executor.submit(perform_checkout, customer_token_2)
        results = [future1.result(), future2.result()]

    status_codes = [r.status_code for r in results]
    print("\nCONCURRENCY TEST RESULTS:")
    for r in results:
        print(f"Status: {r.status_code}, Body: {r.text}")

    # ASSERTION 1: Exactly one succeeded (201) and exactly one failed with conflict (409)
    assert 201 in status_codes, f"Expected one 201 Created in {status_codes}"
    assert 409 in status_codes, f"Expected one 409 Conflict in {status_codes}"

    # ASSERTION 2: The 409 response contains code OUT_OF_STOCK
    conflict_resp = [r for r in results if r.status_code == 409][0]
    conflict_json = conflict_resp.json()
    assert conflict_json["success"] is False
    assert conflict_json["error"]["code"] == "OUT_OF_STOCK"

    # ASSERTION 3: Invariants in database
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        inv = db.query(Inventory).filter(Inventory.product_id == single_stock_product.id).first()
        assert inv.available_quantity == 0, f"Available quantity should be 0, got {inv.available_quantity}"
        assert inv.reserved_quantity == 1, f"Reserved quantity should be 1, got {inv.reserved_quantity}"
        assert inv.sold_quantity == 0, f"Sold quantity should be 0 before payment, got {inv.sold_quantity}"
        assert inv.available_quantity >= 0, "Available quantity must never be negative!"
    finally:
        db.close()
