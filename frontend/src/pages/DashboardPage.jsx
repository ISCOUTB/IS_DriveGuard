import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Eye,
  ListFilter,
  RefreshCw,
  ShieldAlert,
  SlidersHorizontal,
  Tag,
  User,
} from "lucide-react";
import AmbientBackground from "../components/AmbientBackground";
import Navbar from "../components/Navbar";
import SideRail from "../components/SideRail";
import StatCard from "../components/StatCard";
import { formatearFecha, getDashboardData } from "../services/api";

const severityBadge = {
  alta: "badge badge-alta",
  media: "badge badge-media",
  baja: "badge badge-baja",
};

const severityIcon = {
  alta: "text-[#a85448]",
  media: "text-[#a27a34]",
  baja: "text-[#267d69]",
};

function getInitials(name) {
  if (!name) return "—";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "—";
  return parts
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

export default function DashboardPage() {
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const requestIdRef = useRef(0);

  // Filtros
  const [selectedDriver, setSelectedDriver] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("");
  const [selectedReviewed, setSelectedReviewed] = useState("");

  const handleFilterChange = (setter, currentValue) => (event) => {
    const value = event.target.value;
    if (value === currentValue) return;
    setError("");
    setLoading(true);
    setter(value);
  };

  const loadData = useCallback(() => {
    const filters = {};
    if (selectedDriver) filters.conductor_id = selectedDriver;
    if (selectedType) filters.tipo_incidente_id = selectedType;
    if (selectedSeverity) filters.severidad = selectedSeverity;
    if (selectedReviewed !== "") filters.revisado = selectedReviewed === "true";

    const requestId = ++requestIdRef.current;
    getDashboardData(filters)
      .then(({ eventos, resumen, conductores, tipos }) => {
        if (requestId !== requestIdRef.current) return;
        setEvents(eventos);
        setSummary(resumen);
        setDrivers(conductores);
        setTypes(tipos);
        setError("");
      })
      .catch((err) => {
        if (requestId !== requestIdRef.current) return;
        setEvents([]);
        setSummary(null);
        setError(err.message || "No se pudieron cargar los incidentes");
      })
      .finally(() => {
        if (requestId === requestIdRef.current) setLoading(false);
      });
  }, [selectedDriver, selectedType, selectedSeverity, selectedReviewed]);

  const handleManualRefresh = () => {
    setError("");
    setLoading(true);
    loadData();
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  const scrollToFilters = () => {
    const section = document.getElementById("filtros");
    section?.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      section?.querySelector("select")?.focus({ preventScroll: true });
    }, 420);
  };

  const scrollToTable = () => {
    document.getElementById("incidentes")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const totalCount = summary?.total ?? 0;
  const highSeverityCount = summary?.por_severidad?.alta ?? 0;
  const pendingCount = events.filter((e) => !e.revisado).length;

  return (
    <div className="relative min-h-screen text-ink">
      <AmbientBackground />

      <div className="relative z-10 mx-auto w-full max-w-[1500px] px-4 pb-10 pt-4 sm:px-6 lg:pl-[104px] lg:pr-8">
        <Navbar />
        <SideRail
          active="dashboard"
          onRefresh={handleManualRefresh}
          onFilter={scrollToFilters}
          onTable={scrollToTable}
          refreshing={loading}
        />

        <main className="relative mt-7 sm:mt-9">
          {/* Encabezado */}
          <div className="reveal mb-6 flex flex-col justify-between gap-4 sm:mb-8 sm:flex-row sm:items-end">
            <div>
              <h1 className="text-[2rem] font-semibold leading-[1.08] tracking-[-0.035em] text-ink sm:text-[2.35rem]">
                Panel de Incidentes
              </h1>
              <p className="mt-2 max-w-xl text-[12.5px] font-normal leading-relaxed text-ink-muted sm:text-[13px]">
                Monitoreo y revisión de eventos de fatiga registrados en tiempo real
              </p>
            </div>
            <div className="hidden items-center gap-2 sm:flex">
              <span className="glass-chip">
                <span className="h-1.5 w-1.5 rounded-full bg-drive-teal shadow-[0_0_0_3px_rgba(15,144,119,0.13)]" />
                Supervisión
              </span>
            </div>
          </div>

          {/* Tarjetas de Estadísticas */}
          <div className="reveal reveal-delay-1 mb-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-12">
            <StatCard
              variant="hero"
              className="md:col-span-2 xl:col-span-5"
              title="Total de incidentes"
              value={totalCount}
              subtitle="Filtro activo actual"
              accent="amber"
              icon={<ShieldAlert className="h-[18px] w-[18px]" strokeWidth={1.8} />}
              actions={
                <>
                  <button
                    type="button"
                    onClick={handleManualRefresh}
                    disabled={loading}
                    className="btn btn-dark"
                  >
                    <RefreshCw
                      className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
                      strokeWidth={1.9}
                    />
                    <span>Actualizar</span>
                  </button>
                  <button type="button" onClick={scrollToFilters} className="btn btn-glass">
                    <SlidersHorizontal className="h-3.5 w-3.5" strokeWidth={1.9} />
                    <span>Filtrar</span>
                  </button>
                </>
              }
            />
            <StatCard
              variant="light"
              className="xl:col-span-3"
              title="Severidad alta"
              value={highSeverityCount}
              subtitle="Prioridad de atención"
              accent="rose"
              icon={<AlertTriangle className="h-[18px] w-[18px]" strokeWidth={1.8} />}
            />
            <StatCard
              variant="teal"
              className="md:col-span-2 xl:col-span-4"
              title="Pendientes de revisión"
              value={pendingCount}
              subtitle="En los resultados mostrados"
              icon={<Clock className="h-[18px] w-[18px]" strokeWidth={1.8} />}
            />
          </div>

          {/* Barra de Filtros */}
          <section id="filtros" className="glass-panel reveal reveal-delay-2 mb-5 p-5 sm:p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="icon-chip">
                  <SlidersHorizontal className="h-4 w-4" strokeWidth={1.8} />
                </span>
                <h2 className="text-[14px] font-semibold tracking-[-0.015em] text-ink">
                  Filtrar incidentes
                </h2>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div>
                <label className="filter-label">
                  <User className="h-3 w-3" strokeWidth={2} />
                  Conductor
                </label>
                <select
                  value={selectedDriver}
                  onChange={handleFilterChange(setSelectedDriver, selectedDriver)}
                  className="select-glass"
                >
                  <option value="">Todos los conductores</option>
                  {drivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.nombre_completo}
                      {d.numero_licencia ? ` (${d.numero_licencia})` : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="filter-label">
                  <Tag className="h-3 w-3" strokeWidth={2} />
                  Tipo de Incidente
                </label>
                <select
                  value={selectedType}
                  onChange={handleFilterChange(setSelectedType, selectedType)}
                  className="select-glass"
                >
                  <option value="">Todos los tipos</option>
                  {types.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="filter-label">
                  <AlertTriangle className="h-3 w-3" strokeWidth={2} />
                  Severidad
                </label>
                <select
                  value={selectedSeverity}
                  onChange={handleFilterChange(setSelectedSeverity, selectedSeverity)}
                  className="select-glass"
                >
                  <option value="">Todas las severidades</option>
                  <option value="alta">Alta</option>
                  <option value="media">Media</option>
                  <option value="baja">Baja</option>
                </select>
              </div>

              <div>
                <label className="filter-label">
                  <CheckCircle2 className="h-3 w-3" strokeWidth={2} />
                  Estado de Revisión
                </label>
                <select
                  value={selectedReviewed}
                  onChange={handleFilterChange(setSelectedReviewed, selectedReviewed)}
                  className="select-glass"
                >
                  <option value="">Todos los estados</option>
                  <option value="false">Pendiente</option>
                  <option value="true">Revisado</option>
                </select>
              </div>
            </div>
          </section>

          {/* Tabla de Resultados */}
          <section id="incidentes" className="glass-panel reveal reveal-delay-3 overflow-hidden p-4 sm:p-5">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-3 px-1.5 pt-1">
              <div className="flex items-center gap-3">
                <span className="icon-chip">
                  <ListFilter className="h-4 w-4" strokeWidth={1.8} />
                </span>
                <h3 className="text-[14px] font-semibold tracking-[-0.015em] text-ink">
                  Listado de Incidentes
                </h3>
              </div>
              <span className="glass-chip">
                <span className="h-1.5 w-1.5 rounded-full bg-drive-teal" />
                Mostrando {events.length} resultados
              </span>
            </div>

            {error ? (
              <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
                <span className="icon-chip h-11 w-11 text-[#a85448]">
                  <AlertTriangle className="h-5 w-5" strokeWidth={1.8} />
                </span>
                <p className="text-sm font-semibold text-[#8f4439]">{error}</p>
                <p className="max-w-sm text-[11.5px] text-ink-muted">
                  Verifica que la API esté en marcha y vuelve a intentarlo.
                </p>
              </div>
            ) : loading ? (
              <div className="space-y-2 px-0.5 pb-1 pt-2">
                {[0, 1, 2, 3, 4].map((row) => (
                  <div
                    key={row}
                    className="skeleton h-[52px] w-full"
                    style={{ opacity: 1 - row * 0.12 }}
                  />
                ))}
              </div>
            ) : events.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
                <span className="icon-chip h-11 w-11">
                  <ListFilter className="h-5 w-5" strokeWidth={1.8} />
                </span>
                <p className="text-sm font-medium text-ink-soft">
                  No se encontraron incidentes con los filtros seleccionados.
                </p>
              </div>
            ) : (
              <>
                <div className="hidden overflow-x-auto pb-1 md:block">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Fecha y Hora</th>
                        <th>Conductor / Placa</th>
                        <th>Tipo de Incidente</th>
                        <th>Duración</th>
                        <th>Severidad</th>
                        <th>Estado</th>
                        <th className="text-right">Acción</th>
                      </tr>
                    </thead>
                    <tbody>
                      {events.map((e) => (
                        <tr key={e.id}>
                          <td className="whitespace-nowrap text-[11px] font-medium tabular-nums text-ink-soft">
                            {formatearFecha(e.fecha_hora, {
                              dateStyle: "short",
                              timeStyle: "medium",
                            })}
                          </td>
                          <td>
                            <div className="flex items-center gap-2.5">
                              <span className="row-avatar">{getInitials(e.conductor_nombre)}</span>
                              <div className="min-w-0">
                                <div className="max-w-[170px] truncate font-semibold text-ink">
                                  {e.conductor_nombre}
                                </div>
                                <div className="mt-0.5 text-[10.5px] font-normal text-ink-muted">
                                  Vehículo: {e.vehiculo_placa}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td>
                            <div className="flex items-center gap-2.5">
                              <span className="type-mark">
                                <Activity
                                  className={`h-3 w-3 ${severityIcon[e.severidad] ?? "text-ink-muted"}`}
                                  strokeWidth={2}
                                />
                              </span>
                              <span className="max-w-[190px] truncate font-medium text-ink-soft">
                                {e.tipo_incidente_etiqueta || e.tipo_incidente_nombre}
                              </span>
                            </div>
                          </td>
                          <td className="whitespace-nowrap text-[11px] tabular-nums text-ink-muted">
                            {e.duracion_segundos}s
                          </td>
                          <td className="whitespace-nowrap">
                            <span className={severityBadge[e.severidad] ?? "badge badge-neutral"}>
                              {e.severidad}
                            </span>
                          </td>
                          <td className="whitespace-nowrap">
                            {e.revisado ? (
                              <span className="status">
                                <span className="status-dot status-dot--done" />
                                Revisado
                              </span>
                            ) : (
                              <span className="status">
                                <span className="status-dot status-dot--pending" />
                                Pendiente
                              </span>
                            )}
                          </td>
                          <td className="whitespace-nowrap text-right">
                            <Link
                              to={`/incidentes/${e.id}`}
                              className="inline-flex items-center gap-1.5 rounded-full border border-white/60 bg-white/35 px-3 py-1.5 text-[10.5px] font-semibold text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] backdrop-blur-md transition hover:bg-white/55"
                            >
                              <Eye className="h-3 w-3" strokeWidth={1.9} />
                              <span>Ver detalle</span>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="space-y-2.5 md:hidden">
                  {events.map((e) => (
                    <article key={e.id} className="data-card">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 items-center gap-2.5">
                          <span className="row-avatar">{getInitials(e.conductor_nombre)}</span>
                          <div className="min-w-0">
                            <p className="truncate text-[12px] font-semibold text-ink">
                              {e.conductor_nombre}
                            </p>
                            <p className="mt-0.5 text-[10.5px] text-ink-muted">
                              Vehículo: {e.vehiculo_placa}
                            </p>
                          </div>
                        </div>
                        <span className={severityBadge[e.severidad] ?? "badge badge-neutral"}>
                          {e.severidad}
                        </span>
                      </div>

                      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-[11px] text-ink-soft">
                        <span className="inline-flex items-center gap-1.5">
                          <Activity
                            className={`h-3 w-3 ${severityIcon[e.severidad] ?? "text-ink-muted"}`}
                            strokeWidth={2}
                          />
                          {e.tipo_incidente_etiqueta || e.tipo_incidente_nombre}
                        </span>
                        <span className="h-1 w-1 rounded-full bg-ink-muted/40" />
                        <span className="tabular-nums text-ink-muted">{e.duracion_segundos}s</span>
                        <span className="h-1 w-1 rounded-full bg-ink-muted/40" />
                        {e.revisado ? (
                          <span className="status">
                            <span className="status-dot status-dot--done" />
                            Revisado
                          </span>
                        ) : (
                          <span className="status">
                            <span className="status-dot status-dot--pending" />
                            Pendiente
                          </span>
                        )}
                      </div>

                      <div className="mt-3 flex items-center justify-between gap-2 border-t border-white/40 pt-3">
                        <span className="text-[10.5px] font-medium tabular-nums text-ink-muted">
                          {formatearFecha(e.fecha_hora, {
                            dateStyle: "short",
                            timeStyle: "short",
                          })}
                        </span>
                        <Link
                          to={`/incidentes/${e.id}`}
                          className="inline-flex items-center gap-1.5 rounded-full border border-white/60 bg-white/35 px-3 py-1.5 text-[10.5px] font-semibold text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] backdrop-blur-md transition hover:bg-white/55"
                        >
                          <Eye className="h-3 w-3" strokeWidth={1.9} />
                          <span>Ver detalle</span>
                        </Link>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}
