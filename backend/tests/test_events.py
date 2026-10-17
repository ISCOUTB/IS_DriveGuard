"""Pruebas de POST /events (idempotente) y GET /events (filtrado)."""
import datetime
import uuid


def _payload(sesion, tipo):
    return {
        "id": str(uuid.uuid4()),
        "sesion_id": str(sesion.id),
        "tipo_incidente_id": str(tipo.id),
        "fecha_hora": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "duracion_segundos": "2.50",
        "severidad": "alta",
        "valor_metrica": "3.100",
    }


def test_create_event(client, admin_headers, sesion_y_tipo):
    sesion, tipo = sesion_y_tipo
    respuesta = client.post(
        "/events", json=_payload(sesion, tipo), headers=admin_headers
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["sesion_id"] == str(sesion.id)
    assert cuerpo["revisado"] is False


def test_create_event_idempotente_mismo_id(client, admin_headers, sesion_y_tipo):
    sesion, tipo = sesion_y_tipo
    datos = _payload(sesion, tipo)
    primera = client.post("/events", json=datos, headers=admin_headers)
    assert primera.status_code == 201
    segunda = client.post("/events", json=datos, headers=admin_headers)
    # Reintento tras reconexion: no duplica, devuelve el original con 200.
    assert segunda.status_code == 200
    assert segunda.json()["id"] == primera.json()["id"]


def test_create_event_sesion_inexistente(client, admin_headers, sesion_y_tipo):
    _, tipo = sesion_y_tipo
    datos = _payload(sesion_y_tipo[0], tipo)
    datos["sesion_id"] = str(uuid.uuid4())
    respuesta = client.post("/events", json=datos, headers=admin_headers)
    assert respuesta.status_code == 404


def test_filter_events_by_driver(client, admin_headers, sesion_y_tipo):
    sesion, tipo = sesion_y_tipo
    client.post("/events", json=_payload(sesion, tipo), headers=admin_headers)
    respuesta = client.get(
        f"/events?driver={sesion.conductor_id}", headers=admin_headers
    )
    assert respuesta.status_code == 200
    eventos = respuesta.json()
    assert len(eventos) == 1
    # Filtro por otro conductor no trae nada.
    respuesta_vacia = client.get(
        f"/events?driver={uuid.uuid4()}", headers=admin_headers
    )
    assert respuesta_vacia.json() == []


def test_conductor_solo_ve_lo_suyo(client, conductor_headers, sesion_y_tipo):
    sesion, tipo = sesion_y_tipo
    client.post("/events", json=_payload(sesion, tipo), headers=conductor_headers)
    # Aunque pida otro driver, solo recibe sus propios eventos.
    respuesta = client.get(
        f"/events?driver={uuid.uuid4()}", headers=conductor_headers
    )
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1
