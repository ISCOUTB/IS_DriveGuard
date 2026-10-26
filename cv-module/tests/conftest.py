"""Reutiliza fixtures reales del backend sin alterar sus fuentes."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('backend_fixtures', Path(__file__).resolve().parents[2] / 'backend/tests/conftest.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
for name in ('db', 'client', 'crear_usuario', 'auth', 'admin', 'conductor', 'vehiculo', 'tipo', 'sesion'):
    globals()[name] = getattr(fixtures, name)
