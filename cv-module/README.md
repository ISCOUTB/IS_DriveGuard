# Cliente CV de DriveGuard

OpenCV + MediaPipe Face Mesh (468 puntos, inferencia CPU). EAR bilateral,
MAR y pose pitch/yaw/roll con solvePnP; umbrales temporales por reloj monótono.
Un parpadeo corto no dispara eventos. Se registra una vez por episodio de cada
señal; al desaparecer el rostro o interrumpirse los frames se reinician tiempos.
Riesgo: 0 señales=baja/sin alerta, 1=media, 2 o 3=alta; score 0–3.
Los umbrales iniciales son orientativos: calibrar con la cámara y el conductor.

## Ejecutar en un computador local

El módulo corre en un computador con cámara, pantalla y altavoz. No requiere
Raspberry Pi, Docker, cuenta remota ni servidor en producción. Para empezar,
solo usa la cámara y guarda los metadatos localmente; el backend es opcional.

Desde la raíz del repositorio, en Linux/macOS con Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r cv-module/requirements.txt
cd cv-module
python -m driveguard --local-only
```

Se abre la ventana de cámara y la sesión queda activa hasta pulsar `q`.
`--local-only` guarda eventos resumidos en `cv-module/events-local.sqlite3`,
sin solicitar UUID de backend y sin enviar datos por red. Solo incluye UUID,
fecha/hora, tipo de señal, duración, severidad y métrica; no guarda imágenes,
video ni identidad del conductor. El SQLite permanece en el computador. No
subas el archivo de eventos al repositorio.

En Windows, crea el entorno con `py -3.12 -m venv .venv`, activa con
`.venv\Scripts\Activate.ps1`, instala `pip install -r cv-module/requirements.txt`
y ejecuta `cd cv-module; python -m driveguard --local-only`.
MediaPipe 0.10.18 publica wheel ARM64 si en otro momento se necesita, pero el
objetivo de esta prueba es la cámara integrada del computador.

Para comprobar primero las alertas sin abrir la cámara, corre la simulación:

```bash
python -m driveguard --simulate --frames 360 --headless --silent
```

Para salir de la cámara pulsa `q`. Si Windows/macOS/Linux no reconoce la cámara,
prueba otro `camera_index` en `config.local.json`; cámara integrada suele ser 0.
Asegura que ninguna otra aplicación tenga la cámara ocupada. Se puede limitar
la sesión con `--frames 300` mientras ajustas el encuadre. Si no se abre el
altavoz o la cámara, la aplicación informa el error y libera recursos.

El envío al backend se activa solo si se omite `--local-only`, `api_url` apunta
a una API disponible y se configuran UUID existentes de sesión y de los tres
tipos de incidente. Para el ejercicio local basta el modo anterior; la API no
es necesaria para probar detección ni alertas.

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
Conservar `events.sqlite3` al reiniciar y no usar la cola de simulación para eventos reales.
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
escribió la imagen. No equivale a video real ni al rendimiento de la cámara integrada.
La medición de cámara incluye la primera lectura lenta y no detectó rostro; es
un dato de referencia de este mismo PC. Probar la cámara local con el rostro
frente a ella y ajustar el índice si hace falta.
El audio real abrió su stream: primer callback con tono a 18.92 ms tras disparar;
esto mide entrega a PortAudio, no audibilidad física. La simulación ejecuta 12 s
de señales en tiempo virtual sin esperar esos 12 s: sus FPS no son rendimiento CV.
Resultado final: **23 tests pasan**, con un aviso de deprecación de TestClient/httpx
procedente de dependencias del backend. Incluye HTTP loopback con urllib real.
Pendiente para el computador local: probar la sesión con el rostro frente a la cámara integrada y calibrar umbrales. El rendimiento depende de la cámara y la iluminación.
