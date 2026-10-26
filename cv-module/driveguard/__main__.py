"""Ejecutar desde cv-module: python -m driveguard --help."""
import argparse
import json
import logging
import time
import uuid
from dataclasses import replace

from .config import load
from .processing.risk import Detector, Metrics
from .processing.quality import CoverageMonitor, PoseCalibration
from .communication import API, Outbox, SyncWorker, event_payload


def main():
    parser = argparse.ArgumentParser(description='Detección local de fatiga; solo persiste metadatos')
    parser.add_argument('--config', help='Archivo JSON; DG_* tiene precedencia')
    parser.add_argument('--simulate', action='store_true', help='Señales sintéticas, sin cámara ni red')
    parser.add_argument('--benchmark', action='store_true', help='Face Mesh sobre frames negros en memoria; sin cámara/red')
    parser.add_argument('--local-only', action='store_true', help='Cámara, alertas y eventos locales; sin backend/UUID')
    parser.add_argument('--frames', type=int, default=None, help='Fotogramas; por defecto cámara continua, simulación 360')
    parser.add_argument('--headless', action='store_true', help='Sin ventana, solo verificación de rendimiento')
    parser.add_argument('--silent', action='store_true', help='Sin sonido, solo verificación')
    args = parser.parse_args()
    if args.frames is None:
        args.frames = 360 if args.simulate or args.benchmark else 0
    if args.frames < 0 or ((args.simulate or args.benchmark) and args.frames == 0):
        parser.error('La simulación/benchmark requiere --frames > 0')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    config = load(args.config)
    testing = args.simulate or args.benchmark
    local_only = args.local_only and not testing
    if local_only and config.queue_path == 'events.sqlite3':
        config = replace(config, queue_path='events-local.sqlite3')
    if testing:
        # Identidades ficticias exclusivamente para cola local de simulación.
        config = replace(config, session_id=str(uuid.UUID(int=1)), eye_type_id=str(uuid.UUID(int=2)),
                         yawn_type_id=str(uuid.UUID(int=3)), head_type_id=str(uuid.UUID(int=4)))
        if config.queue_path == 'events.sqlite3':
            config = replace(config, queue_path='simulation.sqlite3')
    elif not local_only:
        config.validate_identity()
    from .alerts import Alerts
    detector = Detector(config)
    coverage = CoverageMonitor(config)
    calibration = PoseCalibration()
    outbox = Outbox(config.queue_path)
    worker = SyncWorker(outbox, API(config), config) if config.api_url and not testing and not local_only else None
    alerts = mesh = camera = None
    latencies, capture_times, alert_times = [], [], []
    count = 0
    start = time.perf_counter()
    try:
        alerts = Alerts(config, silent=args.silent)
        if not args.simulate:
            from .processing.mesh import FaceMesh
            mesh = FaceMesh(config)
            if not args.benchmark:
                from .capture import Camera
                camera = Camera(config)
        if worker:
            worker.start()
        start = time.perf_counter()
        while args.frames == 0 or count < args.frames:
            frame_start = time.perf_counter()
            if args.simulate:
                import numpy as np
                frame = np.zeros((config.height, config.width, 3), dtype=np.uint8)
                # 12 s: normal, parpadeo, normal, cierre largo, señales concurrentes, recuperación.
                now = count / config.camera_fps
                phase = now % 12
                metrics = Metrics(0.1 if 1 <= phase < 1.2 or 3 <= phase < 10 else 0.3,
                                  0.8 if 6 <= phase < 10 else 0.2,
                                  30 if 6 <= phase < 10 else 0)
            else:
                import numpy as np
                frame = camera.read() if camera else np.zeros((config.height, config.width, 3), dtype=np.uint8)
                now = time.monotonic()
                metrics = None
            capture_end = time.perf_counter()
            if mesh:
                metrics = mesh.process(frame)
            raw_metrics = metrics
            metrics = calibration.apply(metrics)
            quality = mesh.quality if mesh and not args.benchmark else ''
            risk = detector.update(metrics, now)
            if coverage.update(quality, now):
                alerts.warn_capture()
            detected = time.perf_counter()
            if alerts.trigger(risk):
                alert_times.append((time.perf_counter() - detected) * 1000)
            keep_running = args.headless or alerts.draw(frame, risk, metrics is not None, metrics, quality)
            if not args.headless and alerts.calibrate_requested:
                if raw_metrics is not None and not quality and raw_metrics.ear >= config.ear_threshold:
                    calibration.set(raw_metrics)
                    detector.reset()
                    alerts.calibrated = True
                    logging.info('Postura neutra calibrada; referencia solo en RAM')
                else:
                    logging.warning('Para calibrar: rostro frontal iluminado y ojos abiertos')
            # Ambas alertas preceden al disco; fallar explícitamente si no se puede persistir.
            for signal in risk.new:
                outbox.enqueue(event_payload(config, signal, risk.severity, local_only=local_only))
            if not keep_running:
                break
            capture_times.append((capture_end - frame_start) * 1000)
            latencies.append((time.perf_counter() - frame_start) * 1000)
            count += 1
    finally:
        elapsed = time.perf_counter() - start
        if worker and worker.thread.ident is not None:
            worker.close()
        if camera:
            camera.close()
        if mesh:
            mesh.close()
        if alerts:
            alerts.close()
        if not args.headless:
            import cv2
            cv2.destroyAllWindows()
        if latencies:
            import statistics
            ordered = sorted(latencies)
            report = {'mode': 'simulate-rules' if args.simulate else 'mesh-blank' if args.benchmark else 'local-camera' if local_only else 'camera',
                      'frames': count, 'fps': round(count / elapsed, 2),
                      'frame_mean_ms': round(statistics.mean(latencies), 3),
                      'frame_p95_ms': round(ordered[int((len(ordered)-1)*0.95)], 3),
                      'frame_max_ms': round(max(latencies), 3),
                      'capture_mean_ms': round(statistics.mean(capture_times), 3),
                      'alert_dispatch_max_ms': round(max(alert_times, default=0), 3),
                      'audio_enabled': not args.silent, 'visual_enabled': not args.headless,
                      'pending_events': outbox.count()}
            print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
