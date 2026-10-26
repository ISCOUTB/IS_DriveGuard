import math

import numpy as np
import pytest

from driveguard.config import Config
from driveguard.processing.metrics import ear, mar, head_pose, FACE_MODEL, camera_matrix
from driveguard.processing.risk import Detector, Metrics, Sustained


def test_ear_and_mar():
    assert ear([(0, 0), (1, 1), (3, 1), (4, 0), (3, -1), (1, -1)]) == 0.5
    assert mar([(0, 0), (1, 1), (2, 1), (3, 1), (4, 0), (3, -1), (2, -1), (1, -1)]) == 0.5
    with pytest.raises(ValueError):
        ear([(0, 0)] * 6)
    with pytest.raises(ValueError):
        mar([(0, 0)] * 8)


def test_temporal_blink_and_microsleep():
    gate = Sustained(1.5)
    gate.update(True, 0)
    gate.update(True, 0.2)
    assert not gate.active
    gate.update(False, 0.3)
    gate.update(True, 1)
    gate.update(True, 2.5)
    assert gate.active
    gate.update(False, 2.6)
    assert not gate.active


def advance(detector, metrics, start, seconds):
    result = None
    for t in np.arange(start, start + seconds + 0.05, 0.1):
        result = detector.update(metrics, float(t))
    return result


def test_risk_concurrent_and_one_event_per_episode():
    detector = Detector(Config())
    one = advance(detector, Metrics(0.1, 0.2), 0, 1.6)
    assert one.score == 1 and one.severity == 'media'
    two = advance(detector, Metrics(0.1, 0.8), 1.7, 1.2)
    assert two.score == 2 and two.severity == 'alta'
    three = advance(detector, Metrics(0.1, 0.8, 30), 3, 1.6)
    assert three.score == 3
    assert detector.update(Metrics(0.1, 0.8, 30), 4.7).new == ()
    assert detector.update(None, 4.8).score == 0
    assert detector.update(Metrics(0.1, 0.8, 30), 4.9).score == 0


def test_no_face_gaps_and_nonfinite_reset():
    d = Detector(Config())
    advance(d, Metrics(0.1, 0.2), 0, 1)
    assert d.update(Metrics(0.1, 0.2), 5).score == 0
    assert d.update(Metrics(math.nan, 0.2), 5.1).score == 0
    assert d.update(Metrics(0.1, 0.2), 5.2).score == 0


@pytest.mark.parametrize('angles', [(0, 0, 0), (25, 0, 0), (0, 35, 0), (0, 0, 30), (-25, 0, 0), (0, -35, 0), (0, 0, -30)])
def test_pose_known_projection(angles):
    import cv2
    x, y, z = np.radians(angles)
    rx = np.array(((1, 0, 0), (0, np.cos(x), -np.sin(x)), (0, np.sin(x), np.cos(x))))
    ry = np.array(((np.cos(y), 0, np.sin(y)), (0, 1, 0), (-np.sin(y), 0, np.cos(y))))
    rz = np.array(((np.cos(z), -np.sin(z), 0), (np.sin(z), np.cos(z), 0), (0, 0, 1)))
    rotation, _ = cv2.Rodrigues(rz @ ry @ rx)
    points, _ = cv2.projectPoints(np.array(FACE_MODEL, dtype=float), rotation,
                                 np.array((0., 0., 1500.)), camera_matrix(640, 480), np.zeros(4))
    assert head_pose(points.reshape(-1, 2), 640, 480) == pytest.approx(angles, abs=0.01)


@pytest.mark.parametrize('kwargs', [{'eye_seconds': 0}, {'camera_index': -1}, {'width': 1.5},
                                    {'ear_threshold': float('nan')}, {'tracking_confidence': 2}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)
