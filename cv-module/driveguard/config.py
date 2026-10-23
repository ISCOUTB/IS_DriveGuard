"""Configuración JSON y credenciales exclusivamente en el entorno."""
import json
import math
import os
from dataclasses import dataclass, fields
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True)
class Config:
    camera_index: int = 0
    width: int = 640
    height: int = 480
    camera_fps: int = 30
    ear_threshold: float = 0.21
    eye_seconds: float = 1.5
    mar_threshold: float = 0.60
    yawn_seconds: float = 1.0
    pitch_degrees: float = 20.0
    yaw_degrees: float = 30.0
    roll_degrees: float = 25.0
    head_seconds: float = 1.5
    max_gap_seconds: float = 0.5
    detection_confidence: float = 0.5
    tracking_confidence: float = 0.5
    alert_repeat_seconds: float = 1.0
    tone_hz: int = 880
    tone_seconds: float = 0.20
    sample_rate: int = 44100
    sync_seconds: float = 5.0
    request_timeout: float = 3.0
    sync_batch: int = 50
    queue_path: str = 'events.sqlite3'
    api_url: str = ''
    session_id: str = ''
    eye_type_id: str = ''
    yawn_type_id: str = ''
    head_type_id: str = ''

    def __post_init__(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if f.type in (float, int):
                if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                    raise ValueError(f'{f.name}: número finito requerido')
                if f.type is int and not isinstance(value, int):
                    raise ValueError(f'{f.name}: entero requerido')
                if value < 0 or (f.name != 'camera_index' and value == 0):
                    raise ValueError(f'{f.name}: valor fuera de rango')
            elif not isinstance(value, str):
                raise ValueError(f'{f.name}: texto requerido')
        for name in ('detection_confidence', 'tracking_confidence'):
            if getattr(self, name) > 1:
                raise ValueError(f'{name}: debe ser <= 1')
        if self.tone_hz >= self.sample_rate / 2:
            raise ValueError('tone_hz debe ser menor que Nyquist')

    def validate_identity(self):
        # El conductor se deriva de la sesión en el backend; no se envía otro campo.
        for name in ('session_id', 'eye_type_id', 'yawn_type_id', 'head_type_id'):
            try:
                UUID(getattr(self, name))
            except ValueError as exc:
                raise ValueError(f'Configura {name} con un UUID existente en el backend') from exc


def load(path=None):
    data = json.loads(Path(path).read_text()) if path else {}
    for f in fields(Config):
        raw = os.environ.get('DG_' + f.name.upper())
        if raw is not None:
            data[f.name] = f.type(raw)
    return Config(**data)
