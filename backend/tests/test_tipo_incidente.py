def test_catalogo_visible_para_todos(client, auth, conductor, tipo):
    r = client.get("/tipos-incidentes", headers=auth(conductor))
    assert r.status_code == 200
    assert r.json()[0]["nombre"] == "Somnolencia ocular"
    assert isinstance(r.json()[0]["umbral_sensibilidad"], float)  # numero, no texto


def test_solo_admin_modifica(client, auth, admin, supervisor, tipo):
    nuevo = {"nombre": "Bostezo", "umbral_sensibilidad": 0.6, "unidad_medida": "MAR"}
    assert client.post("/tipos-incidentes", headers=auth(supervisor), json=nuevo).status_code == 403
    assert client.post("/tipos-incidentes", headers=auth(admin), json=nuevo).status_code == 201
    assert client.patch(f"/tipos-incidentes/{tipo.id}", headers=auth(supervisor), json={"umbral_sensibilidad": 0.3}).status_code == 403
    r = client.patch(f"/tipos-incidentes/{tipo.id}", headers=auth(admin), json={"umbral_sensibilidad": 0.3})
    assert r.status_code == 200 and r.json()["umbral_sensibilidad"] == 0.3


def test_validaciones(client, auth, admin, tipo):
    h = auth(admin)
    assert client.post("/tipos-incidentes", headers=h, json={"nombre": tipo.nombre, "umbral_sensibilidad": 1}).status_code == 409
    assert client.post("/tipos-incidentes", headers=h, json={"nombre": "X", "umbral_sensibilidad": 0}).status_code == 422
    assert client.patch(f"/tipos-incidentes/{tipo.id}", headers=h, json={"umbral_sensibilidad": None}).status_code == 422
    assert client.get("/tipos-incidentes/00000000-0000-0000-0000-000000000000", headers=h).status_code == 404