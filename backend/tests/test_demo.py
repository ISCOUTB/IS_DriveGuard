"""El arranque de clase debe ser aislado, repetible y conservar los eventos."""
import importlib.util
from pathlib import Path
import sqlite3


def test_demo_prepare_is_isolated_and_idempotent(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / 'scripts/demo.py'
    spec = importlib.util.spec_from_file_location('class_demo', path)
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///DO_NOT_TOUCH.sqlite3')
    root = tmp_path / '.demo'
    demo.prepare_demo(root)
    demo.prepare_demo(root)
    with sqlite3.connect(root / 'demo.sqlite3') as db:
        assert db.execute('select count(*) from usuarios').fetchone()[0] == 2
        assert db.execute('select count(*) from sesiones').fetchone()[0] == 1
        assert db.execute('select count(*) from tipos_incidentes').fetchone()[0] == 3
        assert db.execute('select count(*) from eventos').fetchone()[0] == 3
    assert not Path('DO_NOT_TOUCH.sqlite3').exists()
