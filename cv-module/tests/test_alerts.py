from driveguard.alerts import Alerts
from driveguard.config import Config
from driveguard.processing.risk import Risk


def test_alert_immediate_repeat_and_callback(monkeypatch):
    import numpy as np
    import sounddevice

    class Stream:
        def __init__(self, **kwargs):
            self.callback = kwargs['callback']
        def start(self):
            pass
        def stop(self):
            pass
        def close(self):
            pass

    monkeypatch.setattr(sounddevice, 'OutputStream', Stream)
    alerts = Alerts(Config())
    risk = Risk(1, 'media', (), ())
    assert alerts.trigger(risk, 0)
    output = np.zeros((256, 1), dtype='float32')
    alerts.stream.callback(output, 256, None, None)
    assert np.max(np.abs(output)) > 0.3
    assert not alerts.trigger(risk, 0.2)
    assert alerts.trigger(risk, 1)
    alerts.close()
