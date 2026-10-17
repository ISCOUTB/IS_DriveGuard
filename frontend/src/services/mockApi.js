/**
 * API simulada (mock) para el dashboard de DriveGuard.
 * Estructurada en alineacion con los esquemas del backend FastAPI (EventoRead, UsuarioRead, etc.).
 */

const MOCK_USUARIO = {
  id: "u1111111-1111-1111-1111-111111111111",
  nombre_completo: "Daniel Sanchez (Supervisor)",
  correo: "supervisor@flota.com",
  rol: "supervisor",
};

const MOCK_DRIVERS = [
  { id: "d2222222-2222-2222-2222-222222222222", nombre: "Carlos Perez", identificacion: "109823412" },
  { id: "d3333333-3333-3333-3333-333333333333", nombre: "Maria Gomez", identificacion: "109854321" },
  { id: "d4444444-4444-4444-4444-444444444444", nombre: "Jorge Martinez", identificacion: "109876543" },
];

const MOCK_INCIDENT_TYPES = [
  { id: "t1111111-1111-1111-1111-111111111111", nombre: "cierre_ojos", etiqueta: "Cierre prolongado de ojos", umbral: 2.5, unidad: "segundos" },
  { id: "t2222222-2222-2222-2222-222222222222", nombre: "bostezo", etiqueta: "Bostezo excesivo", umbral: 3.0, unidad: "segundos" },
  { id: "t3333333-3333-3333-3333-333333333333", nombre: "cabeceo", etiqueta: "Cabeceo / Perdida de postura", umbral: 1.5, unidad: "segundos" },
];

let MOCK_EVENTS = [
  {
    id: "e1000000-0000-0000-0000-000000000001",
    sesion_id: "s1111111-1111-1111-1111-111111111111",
    conductor_id: "d2222222-2222-2222-2222-222222222222",
    conductor_nombre: "Carlos Perez",
    vehiculo_placa: "UUT-456",
    tipo_incidente_id: "t1111111-1111-1111-1111-111111111111",
    tipo_incidente_nombre: "cierre_ojos",
    tipo_incidente_etiqueta: "Cierre prolongado de ojos",
    fecha_hora: "2026-10-17T08:12:00Z",
    fecha_recepcion: "2026-10-17T08:12:03Z",
    duracion_segundos: 3.2,
    severidad: "alta",
    valor_metrica: 0.14,
    comentario_conductor: "Mucha fatiga por turno nocturno.",
    revisado: false,
  },
  {
    id: "e1000000-0000-0000-0000-000000000002",
    sesion_id: "s2222222-2222-2222-2222-222222222222",
    conductor_id: "d3333333-3333-3333-3333-333333333333",
    conductor_nombre: "Maria Gomez",
    vehiculo_placa: "KLS-890",
    tipo_incidente_id: "t2222222-2222-2222-2222-222222222222",
    tipo_incidente_nombre: "bostezo",
    tipo_incidente_etiqueta: "Bostezo excesivo",
    fecha_hora: "2026-10-17T09:45:00Z",
    fecha_recepcion: "2026-10-17T09:45:01Z",
    duracion_segundos: 2.1,
    severidad: "media",
    valor_metrica: 0.68,
    comentario_conductor: null,
    revisado: true,
  },
  {
    id: "e1000000-0000-0000-0000-000000000003",
    sesion_id: "s1111111-1111-1111-1111-111111111111",
    conductor_id: "d2222222-2222-2222-2222-222222222222",
    conductor_nombre: "Carlos Perez",
    vehiculo_placa: "UUT-456",
    tipo_incidente_id: "t3333333-3333-3333-3333-333333333333",
    tipo_incidente_nombre: "cabeceo",
    tipo_incidente_etiqueta: "Cabeceo / Perdida de postura",
    fecha_hora: "2026-10-16T17:30:00Z",
    fecha_recepcion: "2026-10-16T17:30:05Z",
    duracion_segundos: 1.8,
    severidad: "alta",
    valor_metrica: 22.5,
    comentario_conductor: null,
    revisado: false,
  },
  {
    id: "e1000000-0000-0000-0000-000000000004",
    sesion_id: "s3333333-3333-3333-3333-333333333333",
    conductor_id: "d4444444-4444-4444-4444-444444444444",
    conductor_nombre: "Jorge Martinez",
    vehiculo_placa: "WMQ-123",
    tipo_incidente_id: "t1111111-1111-1111-1111-111111111111",
    tipo_incidente_nombre: "cierre_ojos",
    tipo_incidente_etiqueta: "Cierre prolongado de ojos",
    fecha_hora: "2026-10-16T14:10:00Z",
    fecha_recepcion: "2026-10-16T14:10:02Z",
    duracion_segundos: 1.2,
    severidad: "baja",
    valor_metrica: 0.19,
    comentario_conductor: "Parpadeo normal pero lento.",
    revisado: true,
  },
];

export function loginMock(correo, password) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (correo && password) {
        const token = "mock-token-123";
        localStorage.setItem("driveguard_token", token);
        localStorage.setItem("driveguard_user", JSON.stringify(MOCK_USUARIO));
        resolve({ access_token: token, token_type: "bearer", usuario: MOCK_USUARIO });
      } else {
        reject(new Error("Correo y contrasena son requeridos"));
      }
    }, 400);
  });
}

export function logoutMock() {
  localStorage.removeItem("driveguard_token");
  localStorage.removeItem("driveguard_user");
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem("driveguard_token"));
}

export function getCurrentUser() {
  const data = localStorage.getItem("driveguard_user");
  return data ? JSON.parse(data) : MOCK_USUARIO;
}

export function getEventsMock(filters = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let result = [...MOCK_EVENTS];

      if (filters.driver_id) {
        result = result.filter((e) => e.conductor_id === filters.driver_id);
      }
      if (filters.tipo_incidente_id) {
        result = result.filter((e) => e.tipo_incidente_id === filters.tipo_incidente_id);
      }
      if (filters.severidad) {
        result = result.filter((e) => e.severidad === filters.severidad);
      }
      if (typeof filters.revisado === "boolean") {
        result = result.filter((e) => e.revisado === filters.revisado);
      }

      // Ordenar por fecha descedente
      result.sort((a, b) => new Date(b.fecha_hora) - new Date(a.fecha_hora));

      resolve(result);
    }, 300);
  });
}

export function getEventByIdMock(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const event = MOCK_EVENTS.find((e) => e.id === id);
      if (event) {
        resolve({ ...event });
      } else {
        reject(new Error("Incidente no encontrado"));
      }
    }, 300);
  });
}

export function updateEventMock(id, updates) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const idx = MOCK_EVENTS.findIndex((e) => e.id === id);
      if (idx !== -1) {
        MOCK_EVENTS[idx] = {
          ...MOCK_EVENTS[idx],
          ...updates,
        };
        resolve({ ...MOCK_EVENTS[idx] });
      } else {
        reject(new Error("Incidente no encontrado"));
      }
    }, 300);
  });
}

export function getDriversMock() {
  return new Promise((resolve) => resolve([...MOCK_DRIVERS]));
}

export function getIncidentTypesMock() {
  return new Promise((resolve) => resolve([...MOCK_INCIDENT_TYPES]));
}

