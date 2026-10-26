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


def test_capture_warning_has_distinct_double_tone(monkeypatch):
    import numpy as np
    import sounddevice

    class Stream:
        def __init__(self, **kwargs):
            pass
        def start(self):
            pass
        def stop(self):
            pass
        def close(self):
            pass

    monkeypatch.setattr(sounddevice, 'OutputStream', Stream)
    alerts = Alerts(Config())
    alerts.warn_capture()
    output = np.zeros((len(alerts.warning_tone), 1), dtype='float32')
    alerts._callback(output, len(output), None, None)
    rate = alerts.config.sample_rate
    assert np.max(np.abs(output[:int(.1 * rate)])) > .2
    assert np.max(np.abs(output[int(.13 * rate):int(.18 * rate)])) == 0
    assert np.max(np.abs(output[int(.23 * rate):])) > .2
    alerts.close()


def test_switch_warning_to_fatigue_does_not_interrupt_audio(monkeypatch):
    import numpy as np
    import sounddevice
    class Stream:
        def __init__(self, **kwargs):
            pass
        def start(self):
            pass
        def stop(self):
            pass
        def close(self):
            pass
    monkeypatch.setattr(sounddevice, 'OutputStream', Stream)
    alerts = Alerts(Config())
    alerts.warn_capture()
    first = np.zeros((int(alerts.config.sample_rate * .25), 1), dtype='float32')
    alerts._callback(first, len(first), None, None)
    # A main-thread trigger must hand off an entire command. It must not replace
    # the callback's active buffer halfway through the previous waveform.
    previous_buffer = alerts.buffer
    alerts.trigger(Risk(1, 'media', (), ()), 0)
    assert alerts.buffer is previous_buffer
    second = np.zeros((256, 1), dtype='float32')
    alerts._callback(second, len(second), None, None)
    assert np.max(np.abs(second)) > .3
    alerts.close()
