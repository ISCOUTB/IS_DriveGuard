"""Pruebas de POST /auth/login y GET /auth/me."""


def test_login_valid_credentials(client, admin_usuario):
    respuesta = client.post(
        "/auth/login",
        json={"correo": "admin@test.com", "password": "ClaveSegura123"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert "access_token" in cuerpo
    assert cuerpo["token_type"] == "bearer"


def test_login_invalid_credentials(client, admin_usuario):
    respuesta = client.post(
        "/auth/login",
        json={"correo": "admin@test.com", "password": "ClaveIncorrecta"},
    )
    assert respuesta.status_code == 401


def test_login_unknown_email_no_enumera(client):
    # Mismo codigo para correo inexistente (no revela el motivo).
    respuesta = client.post(
        "/auth/login",
        json={"correo": "nadie@test.com", "password": "ClaveSegura123"},
    )
    assert respuesta.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_token(client, admin_headers):
    respuesta = client.get("/auth/me", headers=admin_headers)
    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == "admin@test.com"
