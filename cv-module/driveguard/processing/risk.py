"""Umbrales temporales sobre reloj monótono; un evento por episodio."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    ear: float
    mar: float
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0
    eyes_reliable: bool = True


@dataclass(frozen=True)
class Signal:
    name: str
    duration: float
    value: float


class Sustained:
    def __init__(self, seconds):
        self.seconds = seconds
        self.start = None
        self.active = False

    def update(self, condition, now):
        if not condition:
            self.start, self.active = None, False
            return 0.0
        if self.start is None:
            self.start = now
        duration = now - self.start
        self.active = duration >= self.seconds
        return duration


@dataclass(frozen=True)
class Risk:
    score: int
    severity: str
    active: tuple
    new: tuple


class Detector:
    def __init__(self, config):
        self.config = config
        self.gates = {name: Sustained(seconds) for name, seconds in (
            ('eye', config.eye_seconds), ('yawn', config.yawn_seconds), ('head', config.head_seconds))}
        self.previous = set()
        self.last_time = None

    def update(self, metrics, now):
        import math
        c = self.config
        if self.last_time is not None and (now < self.last_time or now - self.last_time > c.max_gap_seconds):
            self.reset()
        self.last_time = now
        if metrics is None or not all(math.isfinite(v) for v in vars(metrics).values()):
            self.reset()
            return Risk(0, 'baja', (), ())
        values = {'eye': metrics.ear, 'yawn': metrics.mar,
                  'head': max(abs(metrics.pitch), abs(metrics.yaw), abs(metrics.roll))}
        conditions = {'eye': metrics.eyes_reliable and metrics.ear < c.ear_threshold, 'yawn': metrics.mar > c.mar_threshold,
                      'head': abs(metrics.pitch) > c.pitch_degrees or abs(metrics.yaw) > c.yaw_degrees
                      or abs(metrics.roll) > c.roll_degrees}
        active = tuple(Signal(name, gate.update(conditions[name], now), values[name])
                       for name, gate in self.gates.items())
        active = tuple(s for s in active if self.gates[s.name].active)
        names = {s.name for s in active}
        # Una señal=1/media, dos=2/alta, tres=3/alta. Cero=baja sin alerta.
        result = Risk(len(active), 'alta' if len(active) >= 2 else 'media' if active else 'baja',
                      active, tuple(s for s in active if s.name not in self.previous))
        self.previous = names
        return result

    def reset(self):
        for gate in self.gates.values():
            gate.update(False, 0)
        self.previous.clear()
        self.last_time = None
