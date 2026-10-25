# Dashboard (frontend)

Aplicacion React + Vite + TailwindCSS para que los supervisores consulten y
filtren los incidentes registrados.

## Desarrollo

```bash
cd frontend
npm install
npm run dev
```

La app levanta en `http://localhost:5173` con navegacion `/login` <-> `/dashboard`
y consume la API FastAPI en `http://localhost:8000`. Si la API corre en otra URL,
copia `.env.example` a `.env` y ajusta `VITE_API_URL`.

## Estructura

```text
src/
├── components/   # Navbar, PrivateRoute, StatCard
├── pages/        # LoginPage, DashboardPage, IncidentDetailPage
└── services/     # api.js (auth JWT, eventos y catalogos)
```
