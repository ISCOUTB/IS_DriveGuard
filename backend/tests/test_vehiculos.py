def test_crear_normaliza_placa_y_evita_duplicados(client, auth, supervisor):
    h = auth(supervisor)
    r = client.post("/vehiculos", headers=h, json={"placa": " abc999 ", "tipo_vehiculo": "bus"})
    assert r.status_code == 201
    assert r.json()["placa"] == "ABC999" and r.json()["estado"] == "activo"
    assert client.post("/vehiculos", headers=h, json={"placa": "ABC999", "tipo_vehiculo": "camion_carga"}).status_code == 409


def test_conductor_lee_pero_no_escribe(client, auth, conductor, vehiculo):
    h = auth(conductor)
    assert client.get("/vehiculos", headers=h).status_code == 200
    assert client.get(f"/vehiculos/{vehiculo.id}", headers=h).status_code == 200
    assert client.post("/vehiculos", headers=h, json={"placa": "ZZZ111", "tipo_vehiculo": "bus"}).status_code == 403
    assert client.patch(f"/vehiculos/{vehiculo.id}", headers=h, json={"marca": "X"}).status_code == 403


def test_filtros_y_404(client, auth, supervisor, vehiculo):
    h = auth(supervisor)
    assert len(client.get("/vehiculos?estado=activo", headers=h).json()) == 1
    assert client.get("/vehiculos?estado=inactivo", headers=h).json() == []
    assert client.get("/vehiculos/00000000-0000-0000-0000-000000000000", headers=h).status_code == 404


def test_actualizar_y_dar_de_baja(client, auth, supervisor, vehiculo):
    h = auth(supervisor)
    r = client.patch(f"/vehiculos/{vehiculo.id}", headers=h, json={"estado": "mantenimiento", "marca": "Volvo"})
    assert r.status_code == 200 and r.json()["estado"] == "mantenimiento" and r.json()["marca"] == "Volvo"
    assert client.patch(f"/vehiculos/{vehiculo.id}", headers=h, json={"placa": None}).status_code == 422


def test_no_se_da_de_baja_con_sesion_activa(client, auth, supervisor, vehiculo, sesion):
    r = client.patch(f"/vehiculos/{vehiculo.id}", headers=auth(supervisor), json={"estado": "inactivo"})
    assert r.status_code == 409