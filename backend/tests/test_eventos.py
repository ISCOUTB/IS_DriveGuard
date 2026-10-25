import uuid


def _evento(sesion, tipo, **extra):
    datos = {
        "id": str(uuid.uuid4()),
        "sesion_id": sesion["id"],
        "tipo_incidente_id": str(tipo.id),
        "fecha_hora": "2026-10-20T14:30:00Z",
        "duracion_segundos": 2.5,
        "severidad": "media",
        "valor_metrica": 0.182,
    }
    datos.update(extra)
    return datos


def test_registrar_evento_y_reintento_idempotente(client, auth, conductor, sesion, tipo):
    h = auth(conductor)
    ev = _evento(sesion, tipo)
    r1 = client.post("/eventos", headers=h, json=ev)
    assert r1.status_code == 201
    assert r1.json()["id"] == ev["id"] and r1.json()["revisado"] is False
    assert r1.json()["fecha_recepcion"]
    r2 = client.post("/eventos", headers=h, json=ev)  # el cliente reintenta
    assert r2.status_code == 200
    assert r2.json()["id"] == ev["id"]
    assert len(client.get("/eventos", headers=h).json()) == 1  # sin duplicados


def test_los_numeros_salen_como_numeros(client, auth, conductor, sesion, tipo):
    r = client.post("/eventos", headers=auth(conductor), json=_evento(sesion, tipo))
    assert isinstance(r.json()["duracion_segundos"], float)
    assert isinstance(r.json()["valor_metrica"], float)


def test_fecha_con_zona_horaria_se_guarda_en_utc(client, auth, conductor, sesion, tipo):
    ev = _evento(sesion, tipo, fecha_hora="2026-10-20T09:30:00-05:00")
    r = client.post("/eventos", headers=auth(conductor), json=ev)
    assert r.json()["fecha_hora"].startswith("2026-10-20T14:30:00")


def test_id_repetido_en_otra_sesion_es_conflicto(client, auth, conductor, sesion, tipo, crear_usuario, db):
    from app.models import Vehiculo
    from app.models.usuario import RolEnum
    from app.models.vehiculo import TipoVehiculoEnum

    ev = _evento(sesion, tipo)
    assert client.post("/eventos", headers=auth(conductor), json=ev).status_code == 201
    otro = crear_usuario(RolEnum.DRIVER)
    v2 = Vehiculo(placa="QWE456", tipo_vehiculo=TipoVehiculoEnum.BUS)
    db.add(v2)
    db.commit()
    s2 = client.post("/sesiones", headers=auth(otro), json={"conductor_id": str(otro.id), "vehiculo_id": str(v2.id)}).json()
    r = client.post("/eventos", headers=auth(otro), json={**ev, "sesion_id": s2["id"]})
    assert r.status_code == 409


def test_permisos_de_ingesta(client, auth, supervisor, crear_usuario, sesion, tipo):
    from app.models.usuario import RolEnum

    ev = _evento(sesion, tipo)
    assert client.post("/eventos", json=ev).status_code == 401
    assert client.post("/eventos", headers=auth(supervisor), json=ev).status_code == 403
    otro = crear_usuario(RolEnum.DRIVER)
    assert client.post("/eventos", headers=auth(otro), json=ev).status_code == 403  # sesion ajena


def test_referencias_inexistentes_y_validaciones(client, auth, conductor, sesion, tipo):
    h = auth(conductor)
    cero = "00000000-0000-0000-0000-000000000000"
    assert client.post("/eventos", headers=h, json=_evento(sesion, tipo, sesion_id=cero)).status_code == 404
    assert client.post("/eventos", headers=h, json=_evento(sesion, tipo, tipo_incidente_id=cero)).status_code == 404
    assert client.post("/eventos", headers=h, json=_evento(sesion, tipo, duracion_segundos=0)).status_code == 422
    assert client.post("/eventos", headers=h, json=_evento(sesion, tipo, severidad="extrema")).status_code == 422


def test_evento_llega_despues_de_finalizar_la_sesion(client, auth, conductor, sesion, tipo):
    # RNF-02: la cola offline puede vaciarse cuando el turno ya se cerro.
    h = auth(conductor)
    client.post(f"/sesiones/{sesion['id']}/finalizar", headers=h)
    assert client.post("/eventos", headers=h, json=_evento(sesion, tipo)).status_code == 201


def test_lote_mezcla_nuevos_y_duplicados(client, auth, conductor, sesion, tipo):
    h = auth(conductor)
    previos = _evento(sesion, tipo)
    client.post("/eventos", headers=h, json=previos)
    lote = {"eventos": [previos, _evento(sesion, tipo), _evento(sesion, tipo)]}
    r = client.post("/eventos/lote", headers=h, json=lote)
    assert r.status_code == 200
    assert r.json() == {"recibidos": 3, "creados": 2, "duplicados": 1}
    assert len(client.get("/eventos", headers=h).json()) == 3


def test_lote_es_atomico_y_valida_ids_repetidos(client, auth, conductor, sesion, tipo):
    h = auth(conductor)
    cero = "00000000-0000-0000-0000-000000000000"
    malo = _evento(sesion, tipo, tipo_incidente_id=cero)
    r = client.post("/eventos/lote", headers=h, json={"eventos": [_evento(sesion, tipo), malo]})
    assert r.status_code == 404
    assert client.get("/eventos", headers=h).json() == []  # no se guardo ninguno
    repetido = _evento(sesion, tipo)
    assert client.post("/eventos/lote", headers=h, json={"eventos": [repetido, repetido]}).status_code == 422
    assert client.post("/eventos/lote", headers=h, json={"eventos": []}).status_code == 422


def test_filtros_de_consulta(client, auth, conductor, supervisor, sesion, tipo, db):
    from app.models import TipoIncidente

    h = auth(conductor)
    otro_tipo = TipoIncidente(nombre="Bostezo", umbral_sensibilidad=0.6)
    db.add(otro_tipo)
    db.commit()
    client.post("/eventos", headers=h, json=_evento(sesion, tipo, severidad="alta", fecha_hora="2026-10-01T10:00:00Z"))
    client.post("/eventos", headers=h, json=_evento(sesion, otro_tipo, severidad="baja", fecha_hora="2026-10-15T10:00:00Z"))

    s = auth(supervisor)
    assert len(client.get("/eventos", headers=s).json()) == 2
    assert len(client.get("/eventos?severidad=alta", headers=s).json()) == 1
    assert len(client.get(f"/eventos?tipo_incidente_id={otro_tipo.id}", headers=s).json()) == 1
    assert len(client.get("/eventos?desde=2026-10-10T00:00:00Z", headers=s).json()) == 1
    assert len(client.get("/eventos?hasta=2026-10-10T00:00:00Z", headers=s).json()) == 1
    assert len(client.get(f"/eventos?conductor_id={conductor.id}", headers=s).json()) == 2
    assert client.get("/eventos?revisado=true", headers=s).json() == []
    fechas = [e["fecha_hora"] for e in client.get("/eventos", headers=s).json()]
    assert fechas == sorted(fechas, reverse=True)
    assert len(client.get("/eventos?limit=1", headers=s).json()) == 1


def test_un_conductor_solo_ve_sus_eventos(client, auth, conductor, crear_usuario, sesion, tipo):
    from app.models.usuario import RolEnum

    ev = _evento(sesion, tipo)
    client.post("/eventos", headers=auth(conductor), json=ev)
    otro = crear_usuario(RolEnum.DRIVER)
    assert client.get("/eventos", headers=auth(otro)).json() == []
    assert client.get(f"/eventos?conductor_id={conductor.id}", headers=auth(otro)).status_code == 403
    assert client.get(f"/eventos/{ev['id']}", headers=auth(otro)).status_code == 403
    assert client.get(f"/eventos/{ev['id']}", headers=auth(conductor)).status_code == 200
    assert client.get("/eventos/00000000-0000-0000-0000-000000000000", headers=auth(conductor)).status_code == 404


def test_comentar_y_revisar(client, auth, conductor, supervisor, admin, sesion, tipo):
    ev = _evento(sesion, tipo)
    client.post("/eventos", headers=auth(conductor), json=ev)
    url = f"/eventos/{ev['id']}"

    r = client.patch(url, headers=auth(conductor), json={"comentario_conductor": "Estaba cansado"})
    assert r.status_code == 200 and r.json()["comentario_conductor"] == "Estaba cansado"
    assert client.patch(url, headers=auth(conductor), json={"revisado": True}).status_code == 403

    assert client.patch(url, headers=auth(supervisor), json={"comentario_conductor": "x"}).status_code == 403
    r = client.patch(url, headers=auth(supervisor), json={"revisado": True})
    assert r.status_code == 200 and r.json()["revisado"] is True
    assert client.patch(url, headers=auth(supervisor), json={"revisado": None}).status_code == 422
    assert client.patch(url, headers=auth(admin), json={"revisado": False}).status_code == 200


def test_resumen_para_dashboard(client, auth, conductor, supervisor, sesion, tipo):
    h = auth(conductor)
    client.post("/eventos", headers=h, json=_evento(sesion, tipo, severidad="alta", fecha_hora="2026-10-01T10:00:00Z"))
    client.post("/eventos", headers=h, json=_evento(sesion, tipo, severidad="alta", fecha_hora="2026-10-01T11:00:00Z"))
    client.post("/eventos", headers=h, json=_evento(sesion, tipo, severidad="baja", fecha_hora="2026-10-02T11:00:00Z"))

    r = client.get("/eventos/resumen", headers=auth(supervisor))
    assert r.status_code == 200
    datos = r.json()
    assert datos["total"] == 3
    assert datos["por_tipo"] == {"Somnolencia ocular": 3}
    assert datos["por_severidad"] == {"alta": 2, "baja": 1}
    assert datos["por_dia"] == {"2026-10-01": 2, "2026-10-02": 1}
    assert datos["por_conductor"][0]["total"] == 3

    # el conductor ve solo lo suyo y sin desglose por conductor
    propio = client.get("/eventos/resumen", headers=h).json()
    assert propio["total"] == 3 and propio["por_conductor"] == []
    filtrado = client.get("/eventos/resumen?severidad=baja", headers=auth(supervisor)).json()
    assert filtrado["total"] == 1