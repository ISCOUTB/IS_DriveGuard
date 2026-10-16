"""Pruebas del CRUD de /vehicles."""


def test_vehicles_crud_completo(client, admin_headers):
    # Create
    creado = client.post(
        "/vehicles",
        json={"placa": "XYZ999", "tipo_vehiculo": "bus", "marca": "Volvo"},
        headers=admin_headers,
    )
    assert creado.status_code == 201, creado.text
    vehiculo_id = creado.json()["id"]

    # Placa duplicada -> 409
    duplicado = client.post(
        "/vehicles",
        json={"placa": "XYZ999", "tipo_vehiculo": "bus"},
        headers=admin_headers,
    )
    assert duplicado.status_code == 409

    # List + detail
    assert client.get("/vehicles", headers=admin_headers).status_code == 200
    detalle = client.get(f"/vehicles/{vehiculo_id}", headers=admin_headers)
    assert detalle.status_code == 200
    assert detalle.json()["placa"] == "XYZ999"

    # Update
    actualizado = client.patch(
        f"/vehicles/{vehiculo_id}",
        json={"estado": "mantenimiento"},
        headers=admin_headers,
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["estado"] == "mantenimiento"

    # Delete
    assert (
        client.delete(f"/vehicles/{vehiculo_id}", headers=admin_headers).status_code
        == 204
    )
    assert (
        client.get(f"/vehicles/{vehiculo_id}", headers=admin_headers).status_code
        == 404
    )


def test_vehicles_requiere_auth(client):
    assert client.get("/vehicles").status_code == 401
    assert (
        client.post(
            "/vehicles", json={"placa": "AAA111", "tipo_vehiculo": "bus"}
        ).status_code
        == 401
    )
