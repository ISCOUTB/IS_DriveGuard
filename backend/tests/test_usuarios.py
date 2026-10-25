from app.models.usuario import RolEnum


def _nuevo(**kw):
    base = {
        "nombre_completo": "Persona Prueba",
        "correo": "persona@test.com",
        "password": "ClaveSegura1",
        "rol": "supervisor",
    }
    base.update(kw)
    return base


def test_solo_admin_crea_usuarios(client, auth, admin, supervisor, conductor):
    assert client.post("/usuarios", json=_nuevo()).status_code == 401
    assert client.post("/usuarios", headers=auth(supervisor), json=_nuevo()).status_code == 403
    assert client.post("/usuarios", headers=auth(conductor), json=_nuevo()).status_code == 403
    r = client.post("/usuarios", headers=auth(admin), json=_nuevo())
    assert r.status_code == 201
    assert "password" not in r.json() and "contrasena_hash" not in r.json()


def test_conductor_exige_licencia_y_fecha(client, auth, admin):
    r = client.post("/usuarios", headers=auth(admin), json=_nuevo(rol="conductor"))
    assert r.status_code == 422
    ok = client.post(
        "/usuarios",
        headers=auth(admin),
        json=_nuevo(rol="conductor", numero_licencia="L1", fecha_vinculacion="2026-01-01"),
    )
    assert ok.status_code == 201


def test_correo_y_licencia_duplicados(client, auth, admin, conductor):
    assert client.post("/usuarios", headers=auth(admin), json=_nuevo(correo=conductor.correo)).status_code == 409
    r = client.post(
        "/usuarios",
        headers=auth(admin),
        json=_nuevo(rol="conductor", numero_licencia=conductor.numero_licencia, fecha_vinculacion="2026-01-01"),
    )
    assert r.status_code == 409


def test_supervisor_solo_lista_conductores(client, auth, admin, supervisor, conductor):
    assert len(client.get("/usuarios", headers=auth(admin)).json()) == 3
    lista = client.get("/usuarios", headers=auth(supervisor)).json()
    assert [u["rol"] for u in lista] == ["conductor"]
    assert client.get("/usuarios?rol=administrador", headers=auth(supervisor)).status_code == 403
    assert client.get("/usuarios", headers=auth(conductor)).status_code == 403


def test_obtener_usuario_por_rol(client, auth, admin, supervisor, conductor, crear_usuario):
    otro = crear_usuario(RolEnum.DRIVER)
    assert client.get(f"/usuarios/{conductor.id}", headers=auth(conductor)).status_code == 200
    assert client.get(f"/usuarios/{otro.id}", headers=auth(conductor)).status_code == 403
    assert client.get(f"/usuarios/{conductor.id}", headers=auth(supervisor)).status_code == 200
    assert client.get(f"/usuarios/{admin.id}", headers=auth(supervisor)).status_code == 403
    assert client.get("/usuarios/00000000-0000-0000-0000-000000000000", headers=auth(admin)).status_code == 404


def test_actualizar_perfil_propio_limitado(client, auth, conductor):
    h = auth(conductor)
    assert client.patch(f"/usuarios/{conductor.id}", headers=h, json={"telefono": "300"}).json()["telefono"] == "300"
    assert client.patch(f"/usuarios/{conductor.id}", headers=h, json={"activo": False}).status_code == 403
    assert client.patch(f"/usuarios/{conductor.id}", headers=h, json={"numero_licencia": "X"}).status_code == 403


def test_admin_reglas_de_actualizacion(client, auth, admin, supervisor, conductor, crear_usuario):
    h = auth(admin)
    otro = crear_usuario(RolEnum.DRIVER)
    assert client.patch(f"/usuarios/{conductor.id}", headers=h, json={"numero_licencia": None}).status_code == 422
    assert client.patch(f"/usuarios/{conductor.id}", headers=h, json={"numero_licencia": otro.numero_licencia}).status_code == 409
    assert client.patch(f"/usuarios/{supervisor.id}", headers=h, json={"numero_licencia": "L5"}).status_code == 422
    assert client.patch(f"/usuarios/{admin.id}", headers=h, json={"activo": False}).status_code == 422


def test_baja_logica_quita_el_acceso(client, auth, admin, conductor):
    headers_conductor = auth(conductor)
    r = client.patch(f"/usuarios/{conductor.id}", headers=auth(admin), json={"activo": False})
    assert r.status_code == 200 and r.json()["activo"] is False
    assert client.get("/auth/me", headers=headers_conductor).status_code == 401