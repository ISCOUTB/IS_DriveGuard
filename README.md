# Sistema de deteccion de fatiga y somnolencia en conduccion

Proyecto de aula de Ingenieria de Software. Monorepo con los tres modulos del
sistema, cada uno independiente por dentro pero compartiendo el mismo
contrato de API y la misma documentacion.

## Estructura

- `cv-module/` — Modulo de vision por computador (MediaPipe, OpenCV).
- `backend/` — API REST (FastAPI, PostgreSQL).
- `frontend/` — Dashboard de supervision (React).
- `docs/` — Contrato de API (OpenAPI), diagramas UML y documentos del proyecto.

## Como levantar el entorno de desarrollo

Ver `backend/README.md` para instrucciones especificas del backend.
`docker-compose.yml` en la raiz levanta el backend y la base de datos con un
solo comando: `docker-compose up`.

## Equipo

Proyecto desarrollado por un equipo de 3 personas usando Scrum adaptado,
sprints de 2 semanas, sobre 12 semanas totales.
