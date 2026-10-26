# Ajustes de cámara local

Objetivo: mantener alarma por inclinación aislada (elección explícita del usuario), diagnosticar asimetrías y hacer visible cuando la captura no permite evaluar fatiga. Procesamiento local sin guardar imágenes.

Se conserva la regla de postura sostenida independiente de ojos/bostezo. Esa alarma describe postura, no confirma sueño. Se muestran EAR/MAR y ángulos y se permite calibrar una postura neutra con C; no se altera EAR al calibrar. Giro/inclinación extremos impiden inferir ojos pero conservan la señal de cabeza si su pose es calculable.

Imagen de rostro oscura, saturada o sin contraste, rostro ausente o ojos no evaluables: aviso explícito de detección limitada con tono diferente tras 3 segundos y repetición cada 5 segundos. Captura inválida reinicia temporizadores; no se registra como fatiga confirmada. Umbrales son heurísticas configurables iniciales; no prometen visión nocturna ni detectar todos los casos de contraluz.

Alternativas: postura corroborada por cierre/bostezo reduce pitidos con ojos abiertos, pero el usuario eligió mantener alarma por postura sola. Se conserva ese comportamiento y se añade calibración/diagnóstico.

Validación: proyecciones de ángulos positivos y negativos; calibración; calidad de imagen; demora/recuperación de aviso; conservación de alarma de cabeza con ojos no evaluables; pruebas de cola/API y dashboard local con datos ficticios. Confirmación física final pendiente del usuario tras reinicio.
