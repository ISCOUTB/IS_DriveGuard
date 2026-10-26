#!/usr/bin/env python3
"""Demo universitaria local. Nunca abre la cámara sin --camera."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
EMAIL = 'demo@example.com'
PASSWORD = 'DriveGuardDemo1'  # Cuenta ficticia exclusiva de esta demo local.
API_PORT = 8010
FRONT_PORT = 5174


def prepare_demo(data_dir, local_config=None):
    """Crea solo la BD de demo; repetir no borra ni duplica sus registros."""
    from datetime import date, datetime, timezone
    from uuid import uuid4
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.core.security import hash_password
    from app.models import Base, Usuario, Vehiculo, Sesion, TipoIncidente, Evento
    from app.models.usuario import RolEnum
    from app.models.vehiculo import TipoVehiculoEnum
    from app.models.evento import SeveridadEnum

    data_dir.mkdir(parents=True, exist_ok=True)
    data_dir.chmod(0o700)
    database = data_dir / 'demo.sqlite3'
    url = 'sqlite:///' + str(database.resolve())
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            admin = db.scalar(select(Usuario).where(Usuario.correo == EMAIL))
            if admin is None:
                hashed = hash_password(PASSWORD)
                admin = Usuario(nombre_completo='Administrador de demostración', correo=EMAIL,
                                contrasena_hash=hashed, rol=RolEnum.ADMIN)
                driver = Usuario(nombre_completo='Conductor de demostración', correo='conductor@example.com',
                                 contrasena_hash=hashed, rol=RolEnum.DRIVER,
                                 numero_licencia='DEMO-001', fecha_vinculacion=date(2026, 1, 1))
                vehicle = Vehiculo(placa='DEMO01', tipo_vehiculo=TipoVehiculoEnum.BUS)
                kinds = [TipoIncidente(nombre=name, umbral_sensibilidad=value, unidad_medida=unit)
                         for name, value, unit in [('Somnolencia ocular', .21, 'EAR'),
                                                  ('Bostezo', .6, 'MAR'), ('Cabeceo', 20, 'grados')]]
                db.add_all([admin, driver, vehicle, *kinds])
                db.flush()
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                session = Sesion(conductor_id=driver.id, vehiculo_id=vehicle.id, fecha_hora_inicio=now)
                db.add(session)
                db.flush()
                for kind, value in zip(kinds, (.1, .8, 30)):
                    db.add(Evento(id=uuid4(), sesion_id=session.id, tipo_incidente_id=kind.id,
                                  fecha_hora=now, duracion_segundos=2, valor_metrica=value,
                                  severidad=SeveridadEnum.MEDIA,
                                  comentario_conductor='Ejemplo sintético para la demostración en clase.'))
                db.commit()
            session = db.scalar(select(Sesion).order_by(Sesion.fecha_hora_inicio))
            kinds = {t.nombre: str(t.id) for t in db.scalars(select(TipoIncidente))}
            config = {}
            if local_config and local_config.exists():
                config = json.loads(local_config.read_text())
                for key in ('api_url', 'queue_path', 'session_id', 'eye_type_id', 'yawn_type_id', 'head_type_id'):
                    config.pop(key, None)
            config.update(api_url=f'http://127.0.0.1:{API_PORT}', session_id=str(session.id),
                          eye_type_id=kinds['Somnolencia ocular'], yawn_type_id=kinds['Bostezo'],
                          head_type_id=kinds['Cabeceo'], queue_path=str((data_dir / 'outbox.sqlite3').resolve()))
            path = data_dir / 'camera.json'
            path.write_text(json.dumps(config, indent=2) + '\n')
            path.chmod(0o600)
    finally:
        engine.dispose()
    database.chmod(0o600)
    return url, path


def require_port(port):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError as exc:
            raise RuntimeError(f'Puerto {port} ocupado. Cierra la demo anterior; no se abrirá otra instancia.') from exc


def wait_http(url, child):
    for _ in range(100):
        if child.poll() is not None:
            raise RuntimeError('Un servicio terminó antes de iniciar; revisa el error anterior.')
        try:
            with urlopen(url, timeout=.5) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(.1)
    raise RuntimeError(f'No arrancó {url}')


def stop_children(children):
    for child in children:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Preparar datos sin arrancar servicios')
    parser.add_argument('--camera', action='store_true', help='Abrir cámara explícitamente con la API de demo ya activa')
    args = parser.parse_args()
    if args.camera and args.prepare:
        parser.error('Usa --prepare o --camera, no ambos')
    env = os.environ.copy()
    # Aislar esta demo de cualquier configuración de bases o credenciales reales.
    for key in list(env):
        if key.startswith('DG_'):
            del env[key]
    env.update(DG_EMAIL=EMAIL, DG_PASSWORD=PASSWORD)
    if not args.camera and not args.prepare:
        require_port(API_PORT)
        require_port(FRONT_PORT)
        if not shutil.which('npm') or not (ROOT / 'frontend/node_modules').is_dir():
            raise RuntimeError('Ejecuta npm ci dentro de frontend/ antes de arrancar.')
    url, config = prepare_demo(ROOT / '.demo', ROOT / 'cv-module/config.local.json')
    if args.prepare:
        print('Datos de demostración preparados en .demo/. Cámara cerrada.')
        return 0
    if args.camera:
        try:
            with urlopen(f'http://127.0.0.1:{API_PORT}/health', timeout=2):
                pass
        except OSError as exc:
            raise RuntimeError('Primero arranca la demo con python scripts/demo.py') from exc
        # Sin supervisor ni bucle: Q/Ctrl+C termina y no vuelve a abrirla.
        return subprocess.call([sys.executable, '-m', 'driveguard', '--config', str(config)],
                               cwd=ROOT / 'cv-module', env=env)
    env.update(DATABASE_URL=url, SECRET_KEY=secrets.token_hex(32),
               CORS_ORIGINS=f'http://127.0.0.1:{FRONT_PORT},http://localhost:{FRONT_PORT}',
               VITE_API_URL=f'http://127.0.0.1:{API_PORT}')
    children = []
    try:
        children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app',
                                         '--host', '127.0.0.1', '--port', str(API_PORT)],
                                        cwd=ROOT / 'backend', env=env, start_new_session=True))
        wait_http(f'http://127.0.0.1:{API_PORT}/health', children[0])
        children.append(subprocess.Popen(['npm', 'run', 'dev', '--', '--host', '127.0.0.1',
                                         '--port', str(FRONT_PORT), '--strictPort'],
                                        cwd=ROOT / 'frontend', env=env, start_new_session=True))
        wait_http(f'http://127.0.0.1:{FRONT_PORT}', children[1])
        print(f'\nDEMO LISTA: http://127.0.0.1:{FRONT_PORT}\nCuenta ficticia: {EMAIL} / {PASSWORD}\n'
              'Cámara CERRADA. En otra terminal: .venv/bin/python scripts/demo.py --camera\n'
              'Ctrl+C detiene API y panel. Sin reinicio automático.\n', flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.5)
        raise RuntimeError('Un servicio terminó; se detendrán los dos.')
    except KeyboardInterrupt:
        return 0
    finally:
        stop_children(children)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
