"""Calidad heurística de captura y referencia de pose; sin guardar imágenes."""
from dataclasses import replace
import math


def image_quality(frame, config):
    import cv2
    import numpy as np
    if frame.size == 0:
        return 'ROSTRO FUERA DE CUADRO'
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    if mean < config.min_face_brightness:
        return 'POCA LUZ'
    if mean > config.max_face_brightness:
        return 'EXCESO DE LUZ'
    if float(np.percentile(gray, 90) - np.percentile(gray, 10)) < config.min_face_contrast:
        return 'POCO CONTRASTE'
    return ''


class CoverageMonitor:
    def __init__(self, config):
        self.config = config
        self.since = None
        self.last_tone = float('-inf')
        self.last_time = None

    def update(self, reason, now):
        if self.last_time is not None and now < self.last_time:
            self.since = None
            self.last_tone = float('-inf')
        self.last_time = now
        if not reason:
            self.since = None
            self.last_tone = float('-inf')
            return False
        if self.since is None:
            self.since = now
        if now - self.since >= self.config.coverage_seconds and now - self.last_tone >= self.config.coverage_repeat_seconds:
            self.last_tone = now
            return True
        return False


class PoseCalibration:
    def __init__(self):
        self.baseline = (0., 0., 0.)

    def set(self, metrics):
        angles = (metrics.pitch, metrics.yaw, metrics.roll)
        if not metrics.eyes_reliable or not all(math.isfinite(a) for a in angles):
            raise ValueError('Calibrar con rostro frontal y ojos visibles')
        self.baseline = angles

    def apply(self, metrics):
        if metrics is None:
            return None
        angles = [(a - b + 180) % 360 - 180 for a, b in zip(
            (metrics.pitch, metrics.yaw, metrics.roll), self.baseline)]
        return replace(metrics, pitch=angles[0], yaw=angles[1], roll=angles[2])
