"""Outbox SQLite durable + API JWT. Solo se confirma tras 200/201 y mismo UUID."""
import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)


def event_payload(config, signal, severity, *, local_only=False):
    if local_only:
        return {
            'id': str(uuid.uuid4()),
            'fecha_hora': datetime.now(timezone.utc).isoformat(),
            'tipo': signal.name,
            'duracion_segundos': round(min(signal.duration, 999.99), 2),
            'severidad': severity,
            'valor_metrica': round(signal.value, 3),
        }
    return {'id': str(uuid.uuid4()), 'sesion_id': config.session_id,
            'tipo_incidente_id': getattr(config, signal.name + '_type_id'),
            'fecha_hora': datetime.now(timezone.utc).isoformat(),
            'duracion_segundos': round(min(signal.duration, 999.99), 2),
            'severidad': severity, 'valor_metrica': round(signal.value, 3)}


class Outbox:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        # Metadatos personales: permisos restringidos; nunca se guardan tokens.
        os.chmod(self.path, 0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=1)
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, event):
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO events VALUES (?, ?)', (event['id'], json.dumps(event)))

    def pending(self, limit=50):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM events ORDER BY rowid LIMIT ?', (limit,))]

    def acknowledge(self, event_id):
        with self.connect() as db:
            db.execute('DELETE FROM events WHERE id = ?', (event_id,))

    def count(self):
        with self.connect() as db:
            return db.execute('SELECT COUNT(*) FROM events').fetchone()[0]


class API:
    def __init__(self, config, transport=None):
        self.config = config
        self.token = os.environ.get('DG_TOKEN', '')
        self.transport = transport or self._http

    def _http(self, path, data, token=''):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = Request(self.config.api_url.rstrip('/') + path,
                          data=json.dumps(data).encode(), headers=headers, method='POST')
        try:
            with urlopen(request, timeout=self.config.request_timeout) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            # No registrar respuesta: puede contener credenciales o datos personales.
            return exc.code, {}

    def login(self):
        email, password = os.environ.get('DG_EMAIL'), os.environ.get('DG_PASSWORD')
        if not email or not password:
            raise RuntimeError('Falta DG_TOKEN o DG_EMAIL/DG_PASSWORD')
        status, body = self.transport('/auth/login', {'correo': email, 'password': password}, '')
        if status != 200 or not body.get('access_token'):
            raise RuntimeError(f'Login rechazado ({status})')
        self.token = body['access_token']

    def send(self, event):
        if not self.token:
            self.login()
        status, body = self.transport('/events', event, self.token)
        if status == 401 and os.environ.get('DG_EMAIL') and os.environ.get('DG_PASSWORD'):
            self.login()
            status, body = self.transport('/events', event, self.token)
        if status not in (200, 201) or body.get('id') != event['id']:
            raise RuntimeError(f'Evento sin confirmar ({status}); permanece en cola')


def synchronize(outbox, api, limit=50):
    sent = 0
    for event in outbox.pending(limit):
        api.send(event)
        outbox.acknowledge(event['id'])
        sent += 1
    return sent


class SyncWorker:
    def __init__(self, outbox, api, config):
        self.stop_event = threading.Event()
        self.outbox, self.api, self.config = outbox, api, config
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            try:
                synchronize(self.outbox, self.api, self.config.sync_batch)
            except Exception as exc:
                log.warning('Sincronización pendiente (%s)', type(exc).__name__)
            self.stop_event.wait(self.config.sync_seconds)

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=self.config.request_timeout + 0.5)
