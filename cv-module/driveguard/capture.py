"""Captura en memoria; no ofrece ninguna operación de escritura de medios."""


class Camera:
    def __init__(self, config):
        import cv2
        self.capture = cv2.VideoCapture(config.camera_index)
        if not self.capture.isOpened():
            self.capture.release()
            raise RuntimeError(f'No se puede abrir cámara {config.camera_index}')
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
        self.capture.set(cv2.CAP_PROP_FPS, config.camera_fps)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        ok, frame = self.capture.read()
        if not ok:
            raise RuntimeError('Captura interrumpida: no hay fotograma')
        return frame

    def close(self):
        self.capture.release()
