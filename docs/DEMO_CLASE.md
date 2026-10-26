# DriveGuard: demostración en clase (27 de octubre de 2026)

## En este computador

Abre una terminal en la raíz del repositorio y ejecuta:

```bash
.venv/bin/python scripts/demo.py
```

Abre **http://127.0.0.1:5174**. Cuenta ficticia de uso local:
**demo@example.com** / **DriveGuardDemo1**.
La API está en **http://127.0.0.1:8010/docs**.
Este comando inicia backend y frontend; **no abre la cámara**.

Para mostrar detección real, abre otra terminal en la raíz y ejecuta:

```bash
.venv/bin/python scripts/demo.py --camera
```

Usa cámara integrada, micrófono no requerido. Se cargan los ajustes locales de
`cv-module/config.local.json` si existe. No se guardan imágenes ni video.
Con luz frontal y la cara visible, pulsa **C** para fijar postura neutra. Cierra
los ojos unos dos segundos; también puedes bostezar o inclinar la cabeza.
Pulsa **Q** o cierra la ventana con **X** para terminar la cámara; no se reinicia.
Pulsa **Ctrl+C** en la primera terminal para detener API y panel.

## Guion de 3–5 minutos

1. Explica que el objetivo es detectar señales de fatiga: ojos, bostezo y postura.
2. Entra al panel: hay tres ejemplos sintéticos, uno por tipo. Su comentario los
   identifica como ejemplos de clase; no son mediciones de una persona.
3. Abre la cámara explícitamente, calibra con C y genera una señal sostenida.
4. En el panel pulsa **Actualizar** después de unos 5 segundos. Abre el nuevo
   incidente: muestra duración, severidad y métrica. Marca como revisado.
5. Explica que una cola SQLite conserva eventos si la API se desconecta. Las
   alertas locales continúan; vuelve a enviar cuando la API regresa.
6. Muestra captura limitada tapando o dejando sin luz la cámara: el doble tono
   significa que no puede evaluar, no que confirmó sueño.

Si las condiciones de la sala no permiten detección, presenta los tres ejemplos
y aclara que son sintéticos. No atribuyas a la cámara detecciones que no hizo.

## Qué incluye esta demo

- API FastAPI real + dashboard React real + módulo CV real.
- SQLite separado en `.demo/demo.sqlite3`; no modifica bases existentes.
- Cuenta administrador y conductor ficticios, vehículo DEMO01, sesión y catálogo.
- La cámara autentica como la cuenta de demostración y entrega al mismo backend.
- Arranque repetible: conserva eventos y no duplica los tres ejemplos iniciales.
- Base, cola y configuración en `.demo/`, ignorada por Git. Sin contraseñas reales.
- Sin Docker ni despliegue para la clase. El diseño original soporta PostgreSQL;
  **esta demo usa SQLite** y no demuestra PostgreSQL.

La sensibilidad del catálogo es informativa para este cliente; sus umbrales
se cargan de JSON/DG_* al iniciar. Cambiar el catálogo no recalibra la cámara.

## Preparar otro computador (internet para instalar, antes de clase)

Requiere Python 3.12, Node/npm compatibles con frontend (se comprobó con Node 24.19)
y cámara/altavoz. Desde la raíz:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt -r cv-module/requirements.txt
npm --prefix frontend ci
.venv/bin/python scripts/demo.py --prepare
.venv/bin/python scripts/demo.py
```

El lanzador está preparado para Linux/macOS (gestión de procesos POSIX). En
Windows usa los arranques individuales de los README y adapta rutas del entorno.
Si el puerto 8010/5174 está ocupado, termina la demo anterior; el lanzador falla
con un mensaje y no abre instancias adicionales.

## Límites que conviene explicar

Es un prototipo universitario; detecta señales geométricas, no certifica sueño.
Gafas/reflejos, iluminación y cámara requieren calibración. No garantiza detección
en oscuridad o contraluz. Una inclinación sostenida avisa aunque los ojos estén
abiertos (comportamiento elegido). La captura real medida rondó 14.85 FPS con
picos de latencia; no se certifica el objetivo de rendimiento.

La integración con master exige revisión del PR #16 por protección del repositorio.
El código de esta demo está disponible en su rama aunque el merge esté pendiente.
