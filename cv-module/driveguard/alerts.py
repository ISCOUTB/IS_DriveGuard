"""Alerta visual local y tono preinicializado, sin solicitudes de red."""
import time
from queue import SimpleQueue, Empty


class Alerts:
    def __init__(self, config, silent=False):
        self.config = config
        self.silent = silent
        self.last_tone = float('-inf')
        self.remaining = 0
        self.position = 0
        self.stream = None
        self.commands = SimpleQueue()
        self.calibrate_requested = False
        self.calibrated = False
        if not silent:
            import numpy as np
            import sounddevice as sd
            self.tone = (0.35 * np.sin(2 * np.pi * config.tone_hz *
                         np.arange(int(config.sample_rate * config.tone_seconds)) /
                         config.sample_rate)).astype('float32')
            pulse = (0.3 * np.sin(2 * np.pi * 440 * np.arange(int(config.sample_rate * .12)) /
                                 config.sample_rate)).astype('float32')
            self.warning_tone = np.concatenate((pulse, np.zeros(int(config.sample_rate * .1), dtype='float32'), pulse))
            self.buffer = self.tone
            # Abrir antes de capturar: si falla el audio no fingimos una alerta sonora.
            self.stream = sd.OutputStream(samplerate=config.sample_rate, channels=1,
                                          dtype='float32', callback=self._callback, blocksize=256)
            self.stream.start()

    def _callback(self, outdata, frames, timing, status):
        outdata.fill(0)
        # Only the audio callback owns cursor/buffer state. Main thread sends
        # complete precomputed waveforms, so switching tone cannot tear a slice.
        try:
            self.buffer = self.commands.get_nowait()
            self.position = 0
            self.remaining = len(self.buffer)
        except Empty:
            pass
        count = min(frames, self.remaining)
        if count:
            outdata[:count, 0] = self.buffer[self.position:self.position + count]
            self.position += count
            self.remaining -= count

    def trigger(self, risk, now=None):
        now = time.monotonic() if now is None else now
        if risk.score and now - self.last_tone >= self.config.alert_repeat_seconds:
            self.last_tone = now
            if not self.silent:
                self.commands.put(self.tone)
            return True
        return False

    def warn_capture(self):
        if not self.silent:
            self.commands.put(self.warning_tone)

    def draw(self, frame, risk, face_present, metrics=None, quality=''):
        import cv2
        color = (0, 0, 200) if risk.score else (0, 130, 200) if quality else (0, 140, 0)
        if quality:
            text = f'CAPTURA LIMITADA: {quality}'
        else:
            text = f'SENALES {risk.score}/3 {risk.severity.upper()}' if face_present else 'SIN ROSTRO'
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 92), color, -1)
        cv2.putText(frame, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, .52, (255, 255, 255), 1)
        names = {'eye': 'OJOS', 'yawn': 'BOSTEZO', 'head': 'POSTURA'}
        active = ', '.join(names[s.name] for s in risk.active)
        cv2.putText(frame, f'Alertas: {active or "ninguna"}', (8, 47), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
        if metrics:
            eye = f'{metrics.ear:.2f}' if metrics.eyes_reliable else 'N/D'
            values = f'EAR {eye} MAR {metrics.mar:.2f} | P {metrics.pitch:.0f} Y {metrics.yaw:.0f} R {metrics.roll:.0f}'
            cv2.putText(frame, values, (8, 72), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
        footer = 'C: calibrar mirando al frente | Q: salir'
        if self.calibrated:
            footer = 'Postura calibrada | ' + footer
        cv2.rectangle(frame, (0, frame.shape[0] - 28), (frame.shape[1], frame.shape[0]), (25, 25, 25), -1)
        cv2.putText(frame, footer, (8, frame.shape[0] - 9), cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1)
        cv2.imshow('DriveGuard - q para salir', frame)
        key = cv2.waitKey(1) & 0xFF
        self.calibrate_requested = key in (ord('c'), ord('C'))
        return key not in (ord('q'), ord('Q'))

    def close(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
