import numpy as np
from driveguard.config import Config
from driveguard.processing.quality import image_quality, CoverageMonitor, PoseCalibration
from driveguard.processing.risk import Metrics, Detector


def test_dark_flat_and_clipped_capture_is_not_evaluable():
    c = Config()
    assert image_quality(np.zeros((50, 50, 3), dtype=np.uint8), c) == 'POCA LUZ'
    assert image_quality(np.full((50, 50, 3), 255, dtype=np.uint8), c) == 'EXCESO DE LUZ'
    assert image_quality(np.full((50, 50, 3), 100, dtype=np.uint8), c) == 'POCO CONTRASTE'
    gradient = np.tile(np.arange(40, 200, dtype=np.uint8), (50, 1))
    assert image_quality(np.repeat(gradient[..., None], 3, axis=2), c) == ''


def test_coverage_warning_delay_recovery_and_repeat():
    monitor = CoverageMonitor(Config())
    assert not monitor.update('SIN ROSTRO', 0)
    assert not monitor.update('POCA LUZ', 2.9)
    assert monitor.update('POCA LUZ', 3)
    assert not monitor.update('POCA LUZ', 3.1)
    assert monitor.update('POCA LUZ', 8)
    assert not monitor.update('', 8.1)
    assert not monitor.update('SIN ROSTRO', 9)
    assert not monitor.update('SIN ROSTRO', 11.9)


def test_calibration_wraps_pose_symmetrically_without_changing_eyes():
    calibration = PoseCalibration()
    neutral = Metrics(.3, .2, 175, 10, -5)
    calibration.set(neutral)
    result = calibration.apply(Metrics(.3, .2, -175, -20, 25))
    assert (result.pitch, result.yaw, result.roll) == (10, -30, 30)
    assert result.ear == .3


def test_unreliable_eyes_do_not_create_eye_event_but_head_still_alerts():
    detector = Detector(Config())
    result = None
    for now in np.arange(0, 2, .1):
        result = detector.update(Metrics(.1, .2, roll=-35, eyes_reliable=False), float(now))
    assert [s.name for s in result.active] == ['head']
