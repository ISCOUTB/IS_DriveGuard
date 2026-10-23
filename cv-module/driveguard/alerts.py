"""Alerta visual local y tono preinicializado, sin solicitudes de red."""
import time


class Alerts:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent
        self.last_tone = float('-inf')
        self.remaining = 0
        self.position = 0
        self.stream = None
        if not silent:
            import numpy as np
            import sounddevice as sd
            self.tone = (0.35 * np.sin(2 * np.pi * config.tone_hz *
                         np.arange(int(config.sample_rate * config.tone_seconds)) /
                         config.sample_rate)).astype('float32')
            # Abrir antes de capturar: si falla el audio no fingimos una alerta sonora.
            self.stream = sd.OutputStream(samplerate=config.sample_rate, channels=1,
                                          dtype='float32', callback=self._callback, blocksize=256)
            self.stream.start()

    def _callback(self, outdata, frames, timing, status):
        outdata.fill(0)
        count = min(frames, self.remaining)
        if count:
            outdata[:count, 0] = self.tone[self.position:self.position + count]
            self.position += count
            self.remaining -= count

    def trigger(self, risk, now=None):
        now = time.monotonic() if now is None else now
        if risk.score and now - self.last_tone >= self.config.alert_repeat_seconds:
            self.last_tone = now
            if not self.silent:
                self.position = 0
                self.remaining = len(self.tone)
            return True
        return False

    def draw(self, frame, risk, face_present):
        import cv2
        color = (0, 0, 255) if risk.score else (0, 180, 0)
        text = f'RIESGO {risk.score}/3 {risk.severity.upper()}' if face_present else 'SIN ROSTRO: revisar camara'
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 58), color, -1)
        cv2.putText(frame, text, (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.imshow('DriveGuard - q para salir', frame)
        return cv2.waitKey(1) & 0xFF != ord('q')

    def close(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
