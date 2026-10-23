"""Reutiliza fixtures reales del backend sin alterar sus fuentes."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('backend_fixtures', Path(__file__).resolve().parents[2] / 'backend/tests/conftest.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
db_session = fixtures.db_session
client = fixtures.client
admin_usuario = fixtures.admin_usuario
conductor_usuario = fixtures.conductor_usuario
admin_headers = fixtures.admin_headers
sesion_y_tipo = fixtures.sesion_y_tipo
