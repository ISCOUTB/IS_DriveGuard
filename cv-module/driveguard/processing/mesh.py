from .metrics import LEFT_EYE, RIGHT_EYE, MOUTH, POSE_INDICES, ear, mar, head_pose
from .risk import Metrics


class FaceMesh:
    def __init__(self, config):
        import mediapipe as mp
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=False,
            min_detection_confidence=config.detection_confidence,
            min_tracking_confidence=config.tracking_confidence)

    def process(self, frame):
        import cv2
        result = self.mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not result.multi_face_landmarks:
            return None
        height, width = frame.shape[:2]
        landmarks = result.multi_face_landmarks[0].landmark
        points = [(p.x * width, p.y * height) for p in landmarks]
        try:
            return Metrics((ear([points[i] for i in LEFT_EYE]) + ear([points[i] for i in RIGHT_EYE])) / 2,
                           mar([points[i] for i in MOUTH]),
                           *head_pose([points[i] for i in POSE_INDICES], width, height))
        except ValueError:
            return None

    def close(self):
        self.mesh.close()
