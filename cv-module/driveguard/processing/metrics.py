"""Geometría en píxeles (evita distorsión por relación de aspecto)."""
import math

LEFT_EYE = (33, 160, 158, 133, 153, 144)
RIGHT_EYE = (362, 385, 387, 263, 373, 380)
MOUTH = (78, 81, 13, 311, 308, 402, 14, 178)
POSE_INDICES = (1, 152, 33, 263, 61, 291)
# Modelo facial aproximado, ejes x derecha, y abajo, z hacia atrás.
FACE_MODEL = ((0, 0, 0), (0, 330, 65), (-225, -170, 135),
              (225, -170, 135), (-150, 150, 125), (150, 150, 125))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def ear(points):
    if len(points) != 6:
        raise ValueError('EAR necesita seis puntos')
    width = distance(points[0], points[3])
    if width <= 1e-9:
        raise ValueError('Ojo degenerado')
    return (distance(points[1], points[5]) + distance(points[2], points[4])) / (2 * width)


def mar(points):
    if len(points) != 8:
        raise ValueError('MAR necesita ocho puntos')
    width = distance(points[0], points[4])
    if width <= 1e-9:
        raise ValueError('Boca degenerada')
    return sum(distance(points[i], points[8-i]) for i in (1, 2, 3)) / (3 * width)


def camera_matrix(width, height):
    import numpy as np
    return np.array(((width, 0, width / 2), (0, width, height / 2), (0, 0, 1)), dtype=float)


def head_pose(points, width, height):
    import cv2
    import numpy as np
    success, rotation, _ = cv2.solvePnP(
        np.array(FACE_MODEL, dtype=float), np.array(points, dtype=float),
        camera_matrix(width, height), np.zeros((4, 1)), flags=cv2.SOLVEPNP_ITERATIVE)
    if not success:
        raise ValueError('Pose no resuelta')
    matrix, _ = cv2.Rodrigues(rotation)
    angles = cv2.RQDecomp3x3(matrix)[0]
    return tuple(float(a) for a in angles)
