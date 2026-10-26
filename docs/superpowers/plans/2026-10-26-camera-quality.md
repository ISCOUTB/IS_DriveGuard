# Camera quality implementation plan

> **For agentic workers:** Use superpowers:executing-plans in this session.

**Goal:** Distinguir problemas de captura y facilitar calibración manteniendo alarma por postura.
**Architecture:** Calidad de ROI facial antes de inferir métricas; estado explícito y monitor temporal separado de eventos de fatiga; calibración solo de pose en RAM.
**Tech Stack:** Python, OpenCV, MediaPipe, pytest existentes.
**Spec:** docs/superpowers/specs/2026-10-26-camera-quality-design.md

## Global constraints
No guardar imágenes ni credenciales. Mantener alarma por inclinación aislada. No generar incidentes de fatiga por ausencia de imagen. Push autorizado por usuario tras integración.

## Review focus
Oscuridad, saturación, falta de contraste; recuperación sin acumular tiempo; postura lateral positiva/negativa; ojos fuera de plano; calibración sin cambios de EAR.

## Tasks
1. Pruebas en tests/test_quality.py y test_processing.py: calidad de ROI, monitor 3s/5s, calibración angular y ambas direcciones. Ejecutar pruebas fallidas antes de implementación.
2. Implementar processing/quality.py: image_quality(frame, config)->str; CoverageMonitor.update(reason, now)->bool; PoseCalibration.set(metrics)/apply(metrics). Configurar límites en Config. Integrar ROI y ojos fiables en mesh/risk.
3. Integrar estado, valores y tecla C en alerts/__main__; tono de captura diferente del de fatiga. Pruebas de tono y temporización, reiniciar y probar cámara.
4. Verificar suite CV, backend, frontend build/lint, HTTP y dashboard. Documentar limitaciones y reproducibilidad. Revisar diff y hacer commit/push sin imágenes, BD ni datos locales.
