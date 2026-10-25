import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Eye,
  Filter,
  RefreshCw,
} from "lucide-react";
import AmbientBackground from "../components/AmbientBackground";
import Navbar from "../components/Navbar";
import StatCard from "../components/StatCard";
import { formatearFecha, getDashboardData } from "../services/api";

const GLASS_CARD =
  "rounded-3xl border border-white/15 bg-white/[0.07] shadow-[0_8px_40px_0_rgba(0,0,0,0.35),inset_0_1px_1px_0_rgba(255,255,255,0.25)] backdrop-blur-3xl";

const selectClass =
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-xs text-white shadow-inner backdrop-blur-md transition-all focus:border-amber-400/50 focus:bg-white/10 focus:outline-none focus:ring-2 focus:ring-amber-400/30 [&>option]:bg-slate-900";

const labelClass =
  "mb-1.5 block text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55";

const severityBadge = {
  alta: "bg-red-500/15 text-red-200 border-red-400/30",
  media: "bg-amber-500/15 text-amber-200 border-amber-400/30",
  baja: "bg-emerald-500/15 text-emerald-200 border-emerald-400/30",
};

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

  const totalCount = summary?.total ?? 0;
  const highSeverityCount = summary?.por_severidad?.alta ?? 0;
  const pendingCount = events.filter((e) => !e.revisado).length;

  return (
    <div className="relative min-h-screen overflow-hidden text-white">
      <AmbientBackground />
      <Navbar />

      <main className="relative mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        {/* Encabezado */}
        <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-[1.75rem] font-semibold tracking-[-0.02em] text-white drop-shadow-md">
              Panel de Incidentes
            </h1>
            <p className="mt-1 text-sm font-normal text-white/60">
              Monitoreo y revisión de eventos de fatiga registrados en tiempo real
            </p>
          </div>
          <button
            type="button"
            onClick={handleManualRefresh}
            className="inline-flex items-center gap-2 self-start rounded-xl border border-white/15 bg-white/10 px-3.5 py-2 text-xs font-medium text-white/85 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.2)] transition hover:bg-white/20 hover:text-white sm:self-auto"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 text-amber-200/80 ${loading ? "animate-spin" : ""}`}
              strokeWidth={1.75}
            />
            <span>Actualizar</span>
          </button>
        </div>

        {/* Tarjetas de Estadísticas */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            title="Total de incidentes"
            value={totalCount}
            subtitle="Filtro activo actual"
            icon={<AlertTriangle className="h-5 w-5 text-amber-200/80" strokeWidth={1.75} />}
          />
          <StatCard
            title="Severidad alta"
            value={highSeverityCount}
            subtitle="Prioridad de atención"
            icon={<AlertTriangle className="h-5 w-5 text-red-300/90" strokeWidth={1.75} />}
          />
          <StatCard
            title="Pendientes de revisión"
            value={pendingCount}
            subtitle="En los resultados mostrados"
            icon={<Clock className="h-5 w-5 text-amber-200/80" strokeWidth={1.75} />}
          />
        </div>

        {/* Barra de Filtros */}
        <div className={`mb-6 p-5 ${GLASS_CARD}`}>
          <div className="mb-4 flex items-center gap-2 text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55">
            <Filter className="h-3.5 w-3.5 text-amber-200/80" strokeWidth={1.75} />
            <span>Filtrar incidentes</span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className={labelClass}>Conductor</label>
              <select
                value={selectedDriver}
                onChange={handleFilterChange(setSelectedDriver, selectedDriver)}
                className={selectClass}
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
              <label className={labelClass}>Tipo de Incidente</label>
              <select
                value={selectedType}
                onChange={handleFilterChange(setSelectedType, selectedType)}
                className={selectClass}
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
              <label className={labelClass}>Severidad</label>
              <select
                value={selectedSeverity}
                onChange={handleFilterChange(setSelectedSeverity, selectedSeverity)}
                className={selectClass}
              >
                <option value="">Todas las severidades</option>
                <option value="alta">Alta</option>
                <option value="media">Media</option>
                <option value="baja">Baja</option>
              </select>
            </div>

            <div>
              <label className={labelClass}>Estado de Revisión</label>
              <select
                value={selectedReviewed}
                onChange={handleFilterChange(setSelectedReviewed, selectedReviewed)}
                className={selectClass}
              >
                <option value="">Todos los estados</option>
                <option value="false">Pendiente</option>
                <option value="true">Revisado</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tabla de Resultados */}
        <section className={`overflow-hidden ${GLASS_CARD}`}>
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <h3 className="text-[0.9375rem] font-semibold tracking-[-0.01em] text-white/95">
              Listado de Incidentes
            </h3>
            <span className="text-xs font-normal text-white/50">
              Mostrando {events.length} resultados
            </span>
          </div>

          {error ? (
            <div className="flex flex-col items-center justify-center gap-2 p-12 text-center">
              <AlertTriangle className="h-8 w-8 text-red-300" strokeWidth={1.75} />
              <p className="text-sm font-medium text-red-200">{error}</p>
              <p className="text-xs text-white/50">
                Verifica que la API esté en marcha y vuelve a intentarlo.
              </p>
            </div>
          ) : loading ? (
            <div className="flex items-center justify-center p-12 text-sm text-white/60">
              <RefreshCw className="mr-2 h-4 w-4 animate-spin text-amber-200/80" strokeWidth={1.75} />
              Cargando incidentes...
            </div>
          ) : events.length === 0 ? (
            <div className="p-12 text-center text-sm text-white/60">
              No se encontraron incidentes con los filtros seleccionados.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-white/80">
                <thead className="border-b border-white/10 bg-white/[0.04] text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/50">
                  <tr>
                    <th className="px-6 py-3.5 font-semibold">Fecha y Hora</th>
                    <th className="px-6 py-3.5 font-semibold">Conductor / Placa</th>
                    <th className="px-6 py-3.5 font-semibold">Tipo de Incidente</th>
                    <th className="px-6 py-3.5 font-semibold">Duración</th>
                    <th className="px-6 py-3.5 font-semibold">Severidad</th>
                    <th className="px-6 py-3.5 font-semibold">Estado</th>
                    <th className="px-6 py-3.5 text-right font-semibold">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06]">
                  {events.map((e) => (
                    <tr key={e.id} className="transition hover:bg-white/[0.06]">
                      <td className="whitespace-nowrap px-6 py-4 text-xs font-normal tabular-nums text-white/75">
                        {formatearFecha(e.fecha_hora, {
                          dateStyle: "short",
                          timeStyle: "medium",
                        })}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-white">{e.conductor_nombre}</div>
                        <div className="text-xs font-normal text-white/50">Vehículo: {e.vehiculo_placa}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-medium text-white/90">
                          {e.tipo_incidente_etiqueta || e.tipo_incidente_nombre}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-xs tabular-nums text-white/60">
                        {e.duracion_segundos}s
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span
                          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide ${
                            severityBadge[e.severidad] ?? "border-white/15 bg-white/10 text-white/60"
                          }`}
                        >
                          {e.severidad}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {e.revisado ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/15 px-2.5 py-0.5 text-[0.6875rem] font-medium text-emerald-200">
                            <CheckCircle2 className="h-3 w-3" strokeWidth={2} />
                            Revisado
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/30 bg-amber-500/15 px-2.5 py-0.5 text-[0.6875rem] font-medium text-amber-200">
                            <Clock className="h-3 w-3" strokeWidth={2} />
                            Pendiente
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right">
                        <Link
                          to={`/incidentes/${e.id}`}
                          className="inline-flex items-center gap-1.5 rounded-xl border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-amber-100 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.2)] transition hover:bg-white/20 hover:text-white"
                        >
                          <Eye className="h-3.5 w-3.5 text-amber-200/80" strokeWidth={1.75} />
                          <span>Ver detalle</span>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
