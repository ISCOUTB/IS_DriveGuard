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
usando datos mock (`src/services/mockApi.js`) hasta conectar el backend FastAPI.

## Estructura

```text
src/
├── components/   # Navbar, PrivateRoute, StatCard
├── pages/        # LoginPage, DashboardPage
└── services/     # mockApi.js (loginMock, getEventsMock)
```
