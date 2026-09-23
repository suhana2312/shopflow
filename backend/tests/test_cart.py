from decimal import Decimal
from app.models.inventory import Inventory

def test_cart_lifecycle_and_subtotal(client, customer_token, sample_product, db_session):
    # 1. Add item to cart
    add_resp = client.post(
        "/api/v1/cart/items",
        json={"product_id": sample_product.id, "quantity": 2},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert add_resp.status_code == 201
    cart_data = add_resp.json()["data"]
    assert cart_data["total_items"] == 2

    # Expected subtotal = discount_price ($89.99) * 2 = $179.98
    expected_subtotal = Decimal("89.99") * 2
    assert Decimal(str(cart_data["subtotal"])) == expected_subtotal

    # IMPORTANT: Verify inventory was NOT reserved by adding to cart
    inv = db_session.query(Inventory).filter(Inventory.product_id == sample_product.id).first()
    assert inv.available_quantity == 10
    assert inv.reserved_quantity == 0

    # 2. Update item quantity
    item_id = cart_data["items"][0]["id"]
    update_resp = client.patch(
        f"/api/v1/cart/items/{item_id}",
        json={"quantity": 3},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["total_items"] == 3

    # 3. Clear cart
    clear_resp = client.delete(
        "/api/v1/cart",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert clear_resp.status_code == 200
    assert clear_resp.json()["data"]["total_items"] == 0
