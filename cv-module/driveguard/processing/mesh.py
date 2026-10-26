from .metrics import LEFT_EYE, RIGHT_EYE, MOUTH, POSE_INDICES, ear, mar, head_pose, distance
from .risk import Metrics
from .quality import image_quality


class FaceMesh:
    def __init__(self, config):
        import mediapipe as mp
        self.config = config
        self.quality = 'SIN ROSTRO'
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=False,
            min_detection_confidence=config.detection_confidence,
            min_tracking_confidence=config.tracking_confidence)

    def process(self, frame):
        import cv2
        import math
        height, width = frame.shape[:2]
        result = self.mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not result.multi_face_landmarks:
            self.quality = image_quality(frame, self.config) or 'SIN ROSTRO'
            return None
        landmarks = result.multi_face_landmarks[0].landmark
        points = [(p.x * width, p.y * height) for p in landmarks]
        if not all(math.isfinite(v) for p in points for v in p):
            self.quality = 'PUNTOS NO FIABLES'
            return None
        # Examinar el rostro, no el fondo: una ventana brillante no ilumina los ojos.
        x0, x1 = max(0, int(min(p[0] for p in points))), min(width, int(max(p[0] for p in points)) + 1)
        y0, y1 = max(0, int(min(p[1] for p in points))), min(height, int(max(p[1] for p in points)) + 1)
        self.quality = image_quality(frame[y0:y1, x0:x1], self.config)
        if self.quality:
            return None
        try:
            left, right = [points[i] for i in LEFT_EYE], [points[i] for i in RIGHT_EYE]
            pitch, yaw, roll = head_pose([points[i] for i in POSE_INDICES], width, height)
            eye_points = left + right
            reliable = (all(0 <= x < width and 0 <= y < height for x, y in eye_points)
                        and min(distance(left[0], left[3]), distance(right[0], right[3])) >= self.config.min_eye_width
                        and abs(pitch) <= self.config.max_eye_pitch
                        and abs(yaw) <= self.config.max_eye_yaw)
            self.quality = '' if reliable else 'OJOS NO EVALUABLES'
            return Metrics((ear(left) + ear(right)) / 2, mar([points[i] for i in MOUTH]),
                           pitch, yaw, roll, reliable)
        except (ValueError, cv2.error):
            self.quality = 'PUNTOS NO FIABLES'
            return None

    def close(self):
        self.mesh.close()
