from uuid import uuid4
import pytest
from driveguard.config import Config
from driveguard.communication import API, Outbox, event_payload, synchronize
from driveguard.processing.risk import Signal


def payload(config=None):
    return event_payload(config or Config(session_id=str(uuid4()), eye_type_id=str(uuid4())),
                         Signal('eye', 1.5, 0.1), 'media')


def test_durable_queue_deduplicates(tmp_path):
    path = tmp_path / 'queue.sqlite3'
    event = payload()
    outbox = Outbox(path)
    outbox.enqueue(event)
    outbox.enqueue(event)
    assert Outbox(path).pending() == [event]
    assert path.stat().st_mode & 0o777 == 0o600


def test_real_backend_offline_reconnect_lost_ack(client, admin_headers, sesion_y_tipo, tmp_path, monkeypatch):
    session, kind = sesion_y_tipo
    config = Config(session_id=str(session.id), eye_type_id=str(kind.id))
    event = payload(config)
    outbox = Outbox(tmp_path / 'queue.sqlite3')
    outbox.enqueue(event)
    monkeypatch.setenv('DG_TOKEN', admin_headers['Authorization'].split()[1])
    state = {'online': False, 'lose_ack': True}
    statuses = []

    def transport(path, data, token):
        if not state['online']:
            raise ConnectionError('offline')
        response = client.post(path, json=data, headers={'Authorization': f'Bearer {token}'})
        statuses.append(response.status_code)
        if state['lose_ack']:
            state['lose_ack'] = False
            raise TimeoutError('Respuesta perdida tras inserción')
        return response.status_code, response.json()

    api = API(config, transport)
    with pytest.raises(ConnectionError):
        synchronize(outbox, api)
    assert outbox.count() == 1
    state['online'] = True
    with pytest.raises(TimeoutError):
        synchronize(outbox, api)
    assert outbox.count() == 1
    restarted = Outbox(outbox.path)
    assert synchronize(restarted, api) == 1
    assert restarted.count() == 0
    assert statuses == [201, 200]
    response = client.get('/events', headers=admin_headers)
    assert len(response.json()) == 1
    assert response.json()[0]['id'] == event['id']


def test_login_exact_contract_and_expired_token(client, admin_usuario, sesion_y_tipo, tmp_path, monkeypatch):
    session, kind = sesion_y_tipo
    config = Config(session_id=str(session.id), eye_type_id=str(kind.id))
    monkeypatch.setenv('DG_TOKEN', 'expired')
    monkeypatch.setenv('DG_EMAIL', 'admin@test.com')
    monkeypatch.setenv('DG_PASSWORD', 'ClaveSegura123')
    calls = []

    def transport(path, data, token):
        response = client.post(path, json=data, headers={'Authorization': f'Bearer {token}'})
        calls.append((path, response.status_code))
        return response.status_code, response.json()

    outbox = Outbox(tmp_path / 'queue.sqlite3')
    outbox.enqueue(payload(config))
    assert synchronize(outbox, API(config, transport)) == 1
    assert calls == [('/events', 401), ('/auth/login', 200), ('/events', 201)]


@pytest.mark.parametrize('status', [401, 404, 422, 500])
def test_rejected_events_remain_queued(tmp_path, monkeypatch, status):
    monkeypatch.setenv('DG_TOKEN', 'test')
    monkeypatch.delenv('DG_EMAIL', raising=False)
    outbox = Outbox(tmp_path / 'queue.sqlite3')
    outbox.enqueue(payload())
    with pytest.raises(RuntimeError):
        synchronize(outbox, API(Config(), lambda *args: (status, {})))
    assert outbox.count() == 1


def test_wrong_ack_not_removed(tmp_path, monkeypatch):
    monkeypatch.setenv('DG_TOKEN', 'test')
    outbox = Outbox(tmp_path / 'queue.sqlite3')
    outbox.enqueue(payload())
    with pytest.raises(RuntimeError):
        synchronize(outbox, API(Config(), lambda *args: (201, {'id': str(uuid4())})))
    assert outbox.count() == 1


def test_http_transport_real_backend(client, admin_usuario, sesion_y_tipo, tmp_path, monkeypatch):
    """HTTP loopback real: urllib -> login/JWT -> router -> BD aislada."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            response = client.post(self.path, json=data,
                                   headers={'Authorization': self.headers.get('Authorization', '')})
            self.send_response(response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.content)
        def log_message(self, *args):
            pass

    monkeypatch.delenv('DG_TOKEN', raising=False)
    monkeypatch.setenv('DG_EMAIL', 'admin@test.com')
    monkeypatch.setenv('DG_PASSWORD', 'ClaveSegura123')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)
    thread.start()
    try:
        session, kind = sesion_y_tipo
        config = Config(api_url=f'http://127.0.0.1:{server.server_port}',
                        session_id=str(session.id), eye_type_id=str(kind.id))
        outbox = Outbox(tmp_path / 'http.sqlite3')
        outbox.enqueue(payload(config))
        api = API(config)
        assert synchronize(outbox, api) == 1
        assert outbox.count() == 0
        # HTTPError 404 también conserva el evento inválido.
        bad_config = Config(session_id=str(uuid4()), eye_type_id=str(kind.id))
        outbox.enqueue(payload(bad_config))
        with pytest.raises(RuntimeError, match='404'):
            synchronize(outbox, api)
        assert outbox.count() == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
