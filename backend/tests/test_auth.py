def test_register_success(client):
    payload = {
        "email": "newuser@shopflow.io",
        "password": "Password123!",
        "full_name": "New User"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newuser@shopflow.io"
    assert "password" not in data["data"]

def test_register_duplicate_email(client, test_customer_user):
    payload = {
        "email": test_customer_user.email,
        "password": "Password123!",
        "full_name": "Duplicate User"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"

def test_login_success(client, test_customer_user):
    payload = {
        "email": test_customer_user.email,
        "password": "CustomerPass123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

def test_login_invalid_password(client, test_customer_user):
    payload = {
        "email": test_customer_user.email,
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"

def test_refresh_token_rotation(client, test_customer_user):
    # 1. Login to obtain refresh token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_customer_user.email, "password": "CustomerPass123!"}
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # 2. Use refresh token
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()["data"]
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    # Tokens must be rotated
    assert new_data["refresh_token"] != refresh_token

    # 3. Old refresh token must now be revoked
    revoked_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert revoked_resp.status_code == 401

def test_rbac_admin_endpoint(client, customer_token, admin_token):
    # Customer trying to access admin endpoint -> 403 Forbidden
    resp = client.get(
        "/api/v1/admin/metrics",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert resp.status_code == 403

    # Admin accessing admin endpoint -> 200 OK
    resp_admin = client.get(
        "/api/v1/admin/metrics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_admin.status_code == 200
