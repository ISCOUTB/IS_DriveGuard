import datetime


def test_conductor_inicia_su_sesion(sesion, conductor):
    assert sesion["estado"] == "activa"
    assert sesion["conductor_id"] == str(conductor.id)
    assert sesion["fecha_hora_inicio"]


def test_conductor_no_inicia_sesion_de_otro(client, auth, conductor, crear_usuario, vehiculo):
    from app.models.usuario import RolEnum

    otro = crear_usuario(RolEnum.DRIVER)
    r = client.post("/sesiones", headers=auth(conductor), json={"conductor_id": str(otro.id), "vehiculo_id": str(vehiculo.id)})
    assert r.status_code == 403


def test_supervisor_asigna_sesion_a_un_conductor(client, auth, supervisor, conductor, vehiculo):
    r = client.post("/sesiones", headers=auth(supervisor), json={"conductor_id": str(conductor.id), "vehiculo_id": str(vehiculo.id)})
    assert r.status_code == 201


def test_el_conductor_debe_tener_rol_conductor(client, auth, supervisor, vehiculo):
    # Regla que el esquema no puede garantizar: conductor_id debe ser un usuario con rol conductor.
    r = client.post("/sesiones", headers=auth(supervisor), json={"conductor_id": str(supervisor.id), "vehiculo_id": str(vehiculo.id)})
    assert r.status_code == 422


def test_vehiculo_no_activo_y_recursos_inexistentes(client, auth, supervisor, conductor, vehiculo, db):
    from app.models.vehiculo import EstadoVehiculoEnum

    h = auth(supervisor)
    vehiculo.estado = EstadoVehiculoEnum.MANTENIMIENTO
    db.commit()
    assert client.post("/sesiones", headers=h, json={"conductor_id": str(conductor.id), "vehiculo_id": str(vehiculo.id)}).status_code == 422
    cero = "00000000-0000-0000-0000-000000000000"
    assert client.post("/sesiones", headers=h, json={"conductor_id": cero, "vehiculo_id": str(vehiculo.id)}).status_code == 404
    assert client.post("/sesiones", headers=h, json={"conductor_id": str(conductor.id), "vehiculo_id": cero}).status_code == 404


def test_no_dos_sesiones_activas(client, auth, supervisor, sesion, conductor, vehiculo, db):
    from app.models import Vehiculo
    from app.models.usuario import RolEnum
    from app.models.vehiculo import TipoVehiculoEnum

    h = auth(supervisor)
    # mismo conductor, otro vehiculo
    otro_v = Vehiculo(placa="XYZ789", tipo_vehiculo=TipoVehiculoEnum.BUS)
    db.add(otro_v)
    db.commit()
    assert client.post("/sesiones", headers=h, json={"conductor_id": str(conductor.id), "vehiculo_id": str(otro_v.id)}).status_code == 409


def test_no_dos_sesiones_activas_en_el_mismo_vehiculo(client, auth, supervisor, sesion, vehiculo, crear_usuario):
    from app.models.usuario import RolEnum

    otro = crear_usuario(RolEnum.DRIVER)
    r = client.post("/sesiones", headers=auth(supervisor), json={"conductor_id": str(otro.id), "vehiculo_id": str(vehiculo.id)})
    assert r.status_code == 409


def test_listado_y_visibilidad(client, auth, supervisor, conductor, crear_usuario, sesion):
    from app.models.usuario import RolEnum

    otro = crear_usuario(RolEnum.DRIVER)
    assert len(client.get("/sesiones", headers=auth(conductor)).json()) == 1
    assert client.get("/sesiones", headers=auth(otro)).json() == []
    assert client.get(f"/sesiones?conductor_id={conductor.id}", headers=auth(otro)).status_code == 403
    assert client.get(f"/sesiones/{sesion['id']}", headers=auth(otro)).status_code == 403
    assert len(client.get("/sesiones?estado=activa", headers=auth(supervisor)).json()) == 1


def test_finalizar_sesion(client, auth, conductor, sesion):
    h = auth(conductor)
    r = client.post(f"/sesiones/{sesion['id']}/finalizar", headers=h)
    assert r.status_code == 200
    assert r.json()["estado"] == "finalizada" and r.json()["fecha_hora_fin"]
    assert client.post(f"/sesiones/{sesion['id']}/finalizar", headers=h).status_code == 409


def test_finalizar_con_fecha_offline(client, auth, conductor, sesion):
    inicio = datetime.datetime.fromisoformat(sesion["fecha_hora_inicio"])
    fin = (inicio + datetime.timedelta(hours=2)).replace(tzinfo=datetime.timezone.utc).isoformat()
    r = client.post(f"/sesiones/{sesion['id']}/finalizar", headers=auth(conductor), json={"fecha_hora_fin": fin})
    assert r.status_code == 200
    assert r.json()["fecha_hora_fin"].startswith((inicio + datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"))


def test_finalizar_antes_del_inicio_es_invalido(client, auth, conductor, sesion):
    r = client.post(f"/sesiones/{sesion['id']}/finalizar", headers=auth(conductor), json={"fecha_hora_fin": "2000-01-01T00:00:00Z"})
    assert r.status_code == 422


def test_un_conductor_no_finaliza_sesion_ajena(client, auth, crear_usuario, sesion):
    from app.models.usuario import RolEnum

    otro = crear_usuario(RolEnum.DRIVER)
    assert client.post(f"/sesiones/{sesion['id']}/finalizar", headers=auth(otro)).status_code == 403


def test_vehiculo_puede_reutilizarse_tras_finalizar(client, auth, conductor, sesion, vehiculo):
    h = auth(conductor)
    client.post(f"/sesiones/{sesion['id']}/finalizar", headers=h)
    r = client.post("/sesiones", headers=h, json={"conductor_id": str(conductor.id), "vehiculo_id": str(vehiculo.id)})
    assert r.status_code == 201