# Cliente CV de DriveGuard

OpenCV + MediaPipe Face Mesh (468 puntos, inferencia CPU). EAR bilateral,
MAR y pose pitch/yaw/roll con solvePnP; umbrales temporales por reloj monótono.
Un parpadeo corto no dispara eventos. Se registra una vez por episodio de cada
señal; al desaparecer el rostro o interrumpirse los frames se reinician tiempos.
Riesgo: 0 señales=baja/sin alerta, 1=media, 2 o 3=alta; score 0–3.
Los umbrales iniciales son orientativos: calibrar con la cámara y el conductor.

## Instalar y ejecutar

Desde `cv-module/`, Python **3.10–3.12** (Face Mesh legacy fijado a 0.10.18):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.local.json
python -m driveguard --config config.local.json
```

En Linux se requieren cámara V4L2, pantalla local, salida de audio/PortAudio
(p. ej. paquete `libportaudio2` en Debian) y bibliotecas gráficas de OpenCV.
Usar Raspberry Pi OS de 64 bits y comprobar que hay wheel de MediaPipe para
su arquitectura/Python antes de instalar. No se instala PyTorch ni TensorFlow;
MediaPipe incluye su runtime TFLite y declara dependencias transitivas como JAX.
No se agrega Dockerfile: compose solo ejecuta API/PostgreSQL; el cliente usa
cámara, pantalla y altavoz del equipo anfitrión.

Configurar en JSON `session_id`, `eye_type_id`, `yawn_type_id`, `head_type_id`
con UUID **existentes** y `api_url`. El conductor se obtiene de la sesión en el
backend, no de un campo adicional. Actualmente no hay endpoints de sesiones ni
del catálogo de tipos: un responsable debe preparar esos registros en la BD.
No existen identificadores o credenciales de producción en este repositorio.

Credenciales solo en variables de entorno: `DG_TOKEN` (JWT Bearer), o
`DG_EMAIL` y `DG_PASSWORD` para `POST /auth/login` JSON `{correo,password}`.
Si un JWT expira, se vuelve a autenticar si existen las dos credenciales;
con token solo, configurar uno nuevo y reiniciar: los eventos siguen en cola.
No guardar credenciales en JSON ni en Git. Utilizar HTTPS fuera de localhost.
Sin `api_url`, las alertas y el registro local funcionan sin sincronización.

Todos los campos de `Config` admiten `DG_NOMBRE_EN_MAYUSCULAS`, con precedencia
sobre JSON. Principales valores por defecto:

| Configuración | Valor |
|---|---|
| `camera_index`, `width`, `height`, `camera_fps` | 0, 640, 480, 30 (solicitados al dispositivo) |
| `ear_threshold`, `eye_seconds` | 0.21, 1.5 s |
| `mar_threshold`, `yawn_seconds` | 0.60, 1 s |
| `pitch_degrees`, `yaw_degrees`, `roll_degrees`, `head_seconds` | 20°, 30°, 25°, 1.5 s |
| `max_gap_seconds` | 0.5 s (reinicio temporal tras interrupción) |
| `detection_confidence`, `tracking_confidence` | 0.5, 0.5 |
| `alert_repeat_seconds`, `tone_hz`, `tone_seconds`, `sample_rate` | 1 s, 880 Hz, 0.2 s, 44100 Hz |
| `sync_seconds`, `request_timeout`, `sync_batch` | 5 s, 3 s, 50 |
| `queue_path` | events.sqlite3 |

`q` sale; Ctrl+C libera cámara, audio y Face Mesh. `--frames N` limita captura
(por defecto continua). `--headless` y `--silent` son para verificación: desactivan
respectivamente la alerta visual y sonora. En operación se necesitan ambas.
Si no se puede abrir audio o cámara se informa un error y se termina.
No detectar rostro muestra una indicación visual, sin atribuir fatiga.

## Entrega de eventos y privacidad

El UUID se genera antes de persistir el evento en SQLite. Un hilo separado
sincroniza `POST /events` con exactamente `id`, `sesion_id`, `tipo_incidente_id`,
`fecha_hora` (UTC ISO-8601), `duracion_segundos`, `severidad`, `valor_metrica`.
La duración es el tiempo sostenido al dispararse el umbral, no el tiempo total
posterior del episodio; métrica EAR/MAR o máximo ángulo absoluto de cabeza.
Se limita duración a 999.99 s por el Numeric(5,2) del backend.
SQLite solo elimina tras 200/201 con el mismo UUID. Si se pierde una respuesta,
reintenta el mismo UUID: la idempotencia del backend evita duplicados.
Errores de red/auth/404/422 conservan la cola y generan aviso sin volcar payloads;
corregir configuración o credenciales y reiniciar. Un fallo de disco termina
explícitamente tras emitir la alerta local; no se promete persistencia con disco averiado.
Conservar la BD al reiniciar y no reutilizar la cola de simulación en producción.
Solo se almacenan metadatos con permisos 0600: nunca imágenes ni video. Los
frames viven en RAM; tampoco se guardan JWT o contraseñas en la cola.

## Pruebas y medición

```bash
pip install -r requirements-test.txt
python -m pytest -q
python -m driveguard --simulate --frames 360 --headless --silent
python -m driveguard --benchmark --frames 120 --headless --silent
```

Simulación: reloj sintético, parpadeo, cierre largo, bostezos y cabeza inclinada;
no abre cámara ni envía a la API, usa UUID ficticios y `simulation.sqlite3`.
Benchmark: Face Mesh real sobre frames negros en RAM; no representa detección
de un rostro. Ambos generan estadísticas JSON; simulación no mide FPS de cámara.
Las pruebas de integración importan rutas, modelos, login y fixtures reales del
backend con BD SQLite aislada: verifican 201, reintento 200, respuesta perdida,
reinicio de cola, renovación JWT y rechazo sin eliminación. No requieren producción.

Medición del 23-10-2026, Intel i5-8250U x86_64, Python 3.12.14,
MediaPipe 0.10.18, 640×480, 120 frames por prueba, sin ventana ni sonido:

| Recorrido | FPS | Media ms/frame | p95 ms | Máximo ms |
|---|---:|---:|---:|---:|
| Face Mesh + reglas, rostro público repetido en RAM | 63.98 | 15.63 | 21.59 | 46.35 |
| Cámara + Face Mesh + reglas, **sin rostro detectado** | 13.84 | 72.26 | 70.95 | 720.89 |
| Face Mesh sobre frames negros, benchmark CLI | 102.26 | 9.78 | 12.14 | 42.29 |

La prueba con rostro decodificó en RAM la [imagen pública de MediaPipe](https://storage.googleapis.com/mediapipe-assets/portrait.jpg)
y la procesó 120 veces (120 detecciones); excluye captura, GUI y audio. No se
escribió la imagen. No equivale a video real ni a rendimiento en Raspberry Pi.
La cámara incluye la primera lectura lenta; **no cumple ≥15 FPS ni <200 ms en
todos los frames**. No se declara cumplido RNF-01 en hardware objetivo.
El audio real abrió su stream: primer callback con tono a 18.92 ms tras disparar;
esto mide entrega a PortAudio, no audibilidad física. La simulación ejecuta 12 s
de señales en tiempo virtual sin esperar esos 12 s: sus FPS no son rendimiento CV.
Resultado final: **23 tests pasan**, con un aviso de deprecación de TestClient/httpx
procedente de dependencias del backend. Incluye HTTP loopback con urllib real.
Pendiente: configurar URL/JWT/sesión/tipos reales, calibrar y validar captura con
rostro, pantalla y altavoz en Raspberry Pi (≥15 FPS, <200 ms y alerta física <1 s).
