from tests.conftest import PASSWORD


def test_login_valido_devuelve_token(client, supervisor):
    r = client.post("/auth/login", json={"correo": supervisor.correo, "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_contrasena_incorrecta(client, supervisor):
    r = client.post("/auth/login", json={"correo": supervisor.correo, "password": "incorrecta"})
    assert r.status_code == 401


def test_login_correo_inexistente_responde_igual(client, supervisor):
    r = client.post("/auth/login", json={"correo": "nadie@test.com", "password": PASSWORD})
    assert r.status_code == 401
    assert r.json()["detail"] == "Correo o contrasena incorrectos"


def test_login_usuario_inactivo(client, crear_usuario):
    from app.models.usuario import RolEnum

    u = crear_usuario(RolEnum.SUPERVISOR, activo=False)
    assert client.post("/auth/login", json={"correo": u.correo, "password": PASSWORD}).status_code == 401


def test_me_requiere_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_me_devuelve_el_perfil(client, auth, supervisor):
    r = client.get("/auth/me", headers=auth(supervisor))
    assert r.status_code == 200
    assert r.json()["correo"] == supervisor.correo
    assert "contrasena_hash" not in r.json()


def test_usuario_desactivado_pierde_acceso_con_token_vigente(client, auth, supervisor, db):
    headers = auth(supervisor)
    assert client.get("/auth/me", headers=headers).status_code == 200
    supervisor.activo = False
    db.commit()
    assert client.get("/auth/me", headers=headers).status_code == 401