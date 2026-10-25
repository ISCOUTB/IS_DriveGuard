const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const TOKEN_KEY = "driveguard_token";
const USER_KEY = "driveguard_user";

export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function buildQuery(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

function formatDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item.msg === "string") {
          const campo = Array.isArray(item.loc)
            ? item.loc.filter((part) => part !== "body" && part !== "query").join(".")
            : "";
          return campo ? `${campo}: ${item.msg}` : item.msg;
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  return null;
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request(
  path,
  { method = "GET", body, authenticated = true, redirectOn401 = true } = {},
) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const token = localStorage.getItem(TOKEN_KEY);
  if (authenticated && token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      "No se pudo conectar con el servidor. Verifica que la API esté en marcha.",
      0,
    );
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    if (response.status === 401 && authenticated) {
      clearSession();
      if (redirectOn401 && window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    const detail = data && typeof data === "object" ? data.detail : null;
    throw new ApiError(
      formatDetail(detail) || `Error ${response.status} al comunicarse con la API`,
      response.status,
      detail,
    );
  }

  return data;
}

export async function login(correo, password) {
  const token = await request("/auth/login", {
    method: "POST",
    body: { correo, password },
    authenticated: false,
  });

  localStorage.setItem(TOKEN_KEY, token.access_token);
  try {
    const usuario = await request("/auth/me");
    localStorage.setItem(USER_KEY, JSON.stringify(usuario));
    return usuario;
  } catch (error) {
    clearSession();
    throw error;
  }
}

export function logout() {
  clearSession();
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

export function getCurrentUser() {
  const data = localStorage.getItem(USER_KEY);
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function parseFechaUtc(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  const date = new Date(hasTimezone ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatearFecha(value, options) {
  const date = parseFechaUtc(value);
  if (!date) return "—";
  return options ? date.toLocaleString("es-CO", options) : date.toLocaleString("es-CO");
}

export function getEventos(filters = {}) {
  return request(`/eventos${buildQuery({ limit: 200, ...filters })}`);
}

export function getEvento(eventoId) {
  return request(`/eventos/${encodeURIComponent(eventoId)}`);
}

export function updateEvento(eventoId, changes) {
  return request(`/eventos/${encodeURIComponent(eventoId)}`, {
    method: "PATCH",
    body: changes,
  });
}

export function getResumenEventos(filters = {}) {
  const summaryFilters = { ...filters };
  delete summaryFilters.revisado;
  delete summaryFilters.skip;
  delete summaryFilters.limit;
  return request(`/eventos/resumen${buildQuery(summaryFilters)}`);
}

export function getSesiones(filters = {}) {
  return request(`/sesiones${buildQuery({ limit: 100, ...filters })}`);
}

export function getSesion(sesionId) {
  return request(`/sesiones/${encodeURIComponent(sesionId)}`);
}

export function getVehiculos(filters = {}) {
  return request(`/vehiculos${buildQuery({ limit: 100, ...filters })}`);
}

export function getVehiculo(vehiculoId) {
  return request(`/vehiculos/${encodeURIComponent(vehiculoId)}`);
}

export function getUsuariosConductores() {
  return request("/usuarios?rol=conductor&activo=true&limit=100");
}

export function getUsuario(usuarioId) {
  return request(`/usuarios/${encodeURIComponent(usuarioId)}`);
}

export function getTiposIncidente() {
  return request("/tipos-incidentes");
}

function indexById(items) {
  return new Map(items.map((item) => [item.id, item]));
}

export function enriquecerEventos(
  eventos,
  { sesiones = [], vehiculos = [], usuarios = [], tipos = [], usuarioActual = null } = {},
) {
  const sesionesPorId = indexById(sesiones);
  const vehiculosPorId = indexById(vehiculos);
  const usuariosPorId = indexById(usuarios);
  const tiposPorId = indexById(tipos);

  return eventos.map((evento) => {
    const sesion = sesionesPorId.get(evento.sesion_id);
    const tipo = tiposPorId.get(evento.tipo_incidente_id);
    const vehiculo = sesion ? vehiculosPorId.get(sesion.vehiculo_id) : null;
    const conductor = sesion ? usuariosPorId.get(sesion.conductor_id) : null;
    const esUsuarioActual = Boolean(
      sesion && usuarioActual && sesion.conductor_id === usuarioActual.id,
    );

    return {
      ...evento,
      conductor_id: sesion?.conductor_id ?? null,
      conductor_nombre:
        conductor?.nombre_completo ??
        (esUsuarioActual ? usuarioActual.nombre_completo : "Conductor no disponible"),
      vehiculo_placa: vehiculo?.placa ?? "Vehículo no disponible",
      tipo_incidente_nombre: tipo?.nombre ?? "Tipo no disponible",
      tipo_incidente_etiqueta: tipo?.nombre ?? "Tipo no disponible",
    };
  });
}

async function fetchOptional(loader) {
  try {
    return await loader();
  } catch {
    return null;
  }
}

export async function getDashboardData(filters = {}) {
  const usuarioActual = getCurrentUser();
  const [eventos, resumen, sesionesBase, vehiculosBase, tipos, conductores] =
    await Promise.all([
      getEventos(filters),
      getResumenEventos(filters),
      getSesiones(),
      getVehiculos(),
      getTiposIncidente(),
      getUsuariosConductores().catch((error) => {
        if (error instanceof ApiError && error.status === 403) return [];
        throw error;
      }),
    ]);

  const sesiones = [...sesionesBase];
  const sesionesConocidas = new Set(sesiones.map((sesion) => sesion.id));
  const sesionesFaltantes = [
    ...new Set(eventos.map((evento) => evento.sesion_id)),
  ].filter((id) => !sesionesConocidas.has(id));
  if (sesionesFaltantes.length) {
    const extras = await Promise.all(
      sesionesFaltantes.map((id) => fetchOptional(() => getSesion(id))),
    );
    sesiones.push(...extras.filter(Boolean));
  }

  const vehiculos = [...vehiculosBase];
  const vehiculosConocidos = new Set(vehiculos.map((vehiculo) => vehiculo.id));
  const vehiculosFaltantes = [
    ...new Set(sesiones.map((sesion) => sesion.vehiculo_id)),
  ].filter((id) => !vehiculosConocidos.has(id));
  if (vehiculosFaltantes.length) {
    const extras = await Promise.all(
      vehiculosFaltantes.map((id) => fetchOptional(() => getVehiculo(id))),
    );
    vehiculos.push(...extras.filter(Boolean));
  }

  const usuarios = [...conductores];
  const usuariosConocidos = new Set(usuarios.map((usuario) => usuario.id));
  const usuariosFaltantes = [
    ...new Set(sesiones.map((sesion) => sesion.conductor_id)),
  ].filter(
    (id) =>
      !usuariosConocidos.has(id) && (!usuarioActual || id !== usuarioActual.id),
  );
  if (usuariosFaltantes.length) {
    const extras = await Promise.all(
      usuariosFaltantes.map((id) => fetchOptional(() => getUsuario(id))),
    );
    usuarios.push(...extras.filter(Boolean));
  }

  return {
    eventos: enriquecerEventos(eventos, {
      sesiones,
      vehiculos,
      usuarios,
      tipos,
      usuarioActual,
    }),
    resumen,
    conductores,
    tipos,
  };
}

export async function getEventoDetallado(eventoId) {
  const [evento, tipos] = await Promise.all([
    getEvento(eventoId),
    getTiposIncidente(),
  ]);
  const sesion = await fetchOptional(() => getSesion(evento.sesion_id));

  const [vehiculo, conductor] = sesion
    ? await Promise.all([
        fetchOptional(() => getVehiculo(sesion.vehiculo_id)),
        fetchOptional(() => getUsuario(sesion.conductor_id)),
      ])
    : [null, null];

  return enriquecerEventos([evento], {
    sesiones: sesion ? [sesion] : [],
    vehiculos: vehiculo ? [vehiculo] : [],
    usuarios: conductor ? [conductor] : [],
    tipos,
    usuarioActual: getCurrentUser(),
  })[0];
}
