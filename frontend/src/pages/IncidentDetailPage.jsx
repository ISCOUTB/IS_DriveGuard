import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Car,
  CheckCircle2,
  Clock,
  Gauge,
  MessageSquare,
  ShieldCheck,
  User,
} from "lucide-react";
import AmbientBackground from "../components/AmbientBackground";
import Navbar from "../components/Navbar";
import {
  formatearFecha,
  getCurrentUser,
  getEventoDetallado,
  updateEvento,
} from "../services/api";

const GLASS_CARD =
  "rounded-3xl border border-white/15 bg-white/[0.07] shadow-[0_8px_40px_0_rgba(0,0,0,0.35),inset_0_1px_1px_0_rgba(255,255,255,0.25)] backdrop-blur-3xl";

const labelClass =
  "text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55";

const severityBadge = {
  alta: "bg-red-500/15 text-red-200 border-red-400/30",
  media: "bg-amber-500/15 text-amber-200 border-amber-400/30",
  baja: "bg-emerald-500/15 text-emerald-200 border-emerald-400/30",
};

export default function IncidentDetailPage() {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState(false);
  const actual = getCurrentUser();
  const puedeRevisar =
    actual?.rol === "supervisor" || actual?.rol === "administrador";

  useEffect(() => {
    let isMounted = true;
    getEventoDetallado(id)
      .then((data) => {
        if (isMounted) setEvent(data);
      })
      .catch((err) => {
        if (isMounted) setError(err.message);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  const toggleReviewedStatus = async () => {
    if (!event) return;
    setUpdating(true);
    try {
      const updated = await updateEvento(event.id, {
        revisado: !event.revisado,
      });
      setEvent((prev) => ({ ...prev, ...updated }));
    } catch (err) {
      alert("Error al actualizar estado del incidente: " + err.message);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden text-white">
      <AmbientBackground />
      <Navbar />

      <main className="relative mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <Link
          to="/dashboard"
          className="mb-6 inline-flex items-center gap-2 text-xs font-medium text-white/60 transition hover:text-amber-100"
        >
          <ArrowLeft className="h-4 w-4" strokeWidth={1.75} />
          <span>Volver al panel de incidentes</span>
        </Link>

        {loading ? (
          <div className={`p-12 text-center text-sm text-white/60 ${GLASS_CARD}`}>
            Cargando detalle del incidente...
          </div>
        ) : error ? (
          <div className="rounded-3xl border border-red-400/30 bg-red-500/10 p-8 text-center text-red-200 backdrop-blur-3xl">
            <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-300" strokeWidth={1.75} />
            <p className="font-medium">{error}</p>
          </div>
        ) : event ? (
          <div className="space-y-6">
            {/* Encabezado del Incidente */}
            <div className={`p-6 ${GLASS_CARD}`}>
              <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h1 className="text-[1.75rem] font-semibold tracking-[-0.02em] text-white">
                      {event.tipo_incidente_etiqueta || event.tipo_incidente_nombre}
                    </h1>
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide ${
                        severityBadge[event.severidad]
                      }`}
                    >
                      Severidad {event.severidad}
                    </span>
                    {event.revisado ? (
                      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/15 px-2.5 py-0.5 text-[0.6875rem] font-medium text-emerald-200">
                        <CheckCircle2 className="h-3.5 w-3.5" strokeWidth={2} />
                        Revisado
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/30 bg-amber-500/15 px-2.5 py-0.5 text-[0.6875rem] font-medium text-amber-200">
                        <Clock className="h-3.5 w-3.5" strokeWidth={2} />
                        Pendiente de revisión
                      </span>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-4 text-xs font-normal text-white/55">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-amber-200/70" strokeWidth={1.75} />
                      Ocurrencia:{" "}
                      <strong className="font-medium text-white/90">
                        {formatearFecha(event.fecha_hora)}
                      </strong>
                    </span>
                    <span className="text-white/25">•</span>
                    <span>
                      Sincronizado:{" "}
                      <strong className="font-medium text-white/90">
                        {formatearFecha(event.fecha_recepcion)}
                      </strong>
                    </span>
                  </div>
                </div>

                {puedeRevisar && (
                  <button
                    type="button"
                    onClick={toggleReviewedStatus}
                    disabled={updating}
                    className={`inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-semibold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.25)] transition disabled:opacity-50 ${
                      event.revisado
                        ? "border-white/15 bg-white/10 text-white/85 hover:bg-white/20"
                        : "border-amber-300/50 bg-gradient-to-br from-amber-300/90 to-amber-500/90 text-slate-950 shadow-[0_4px_20px_0_rgba(245,158,11,0.4)] hover:from-amber-200 hover:to-amber-400"
                    }`}
                  >
                    <ShieldCheck className="h-4 w-4" strokeWidth={1.75} />
                    <span>
                      {updating
                        ? "Guardando..."
                        : event.revisado
                        ? "Marcar como pendiente"
                        : "Marcar como revisado"}
                    </span>
                  </button>
                )}
              </div>
            </div>

            {/* Métricas Clave */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: Clock, label: "Duración", value: event.duracion_segundos, unit: "segundos", mono: false },
                { icon: Gauge, label: "Métrica calculada", value: event.valor_metrica, unit: null, mono: true },
                { icon: User, label: "Conductor", value: event.conductor_nombre, unit: null, mono: false, small: true },
                { icon: Car, label: "Vehículo asignado", value: event.vehiculo_placa, unit: null, mono: false, small: true },
              ].map(({ icon: Icon, label, value, unit, mono, small }) => (
                <div
                  key={label}
                  className="rounded-3xl border border-white/15 bg-gradient-to-br from-white/15 via-white/5 to-white/[0.02] p-5 shadow-[0_8px_40px_0_rgba(0,0,0,0.35),inset_0_1px_1px_0_rgba(255,255,255,0.25)] backdrop-blur-3xl"
                >
                  <div className="flex items-center gap-2">
                    <div className="rounded-lg border border-white/20 bg-white/10 p-1.5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.3)]">
                      <Icon className="h-3.5 w-3.5 text-amber-200/85" strokeWidth={1.75} />
                    </div>
                    <span className={labelClass}>{label}</span>
                  </div>
                  <p
                    className={`mt-3 font-semibold tracking-[-0.01em] text-white ${
                      small ? "text-lg" : "text-2xl"
                    } ${mono ? "font-mono" : ""} ${mono ? "" : "tabular-nums"}`}
                  >
                    {value}
                    {unit && <span className="ml-1.5 text-sm font-normal text-white/50">{unit}</span>}
                  </p>
                </div>
              ))}
            </div>

            {/* Comentario del Conductor */}
            <div className={`p-6 ${GLASS_CARD}`}>
              <h3 className="mb-3 flex items-center gap-2 text-[0.9375rem] font-semibold tracking-[-0.01em] text-white/95">
                <MessageSquare className="h-4 w-4 text-amber-200/80" strokeWidth={1.75} />
                <span>Comentario registrado por el conductor</span>
              </h3>
              {event.comentario_conductor ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-sm font-normal italic text-white/80 shadow-inner">
                  "{event.comentario_conductor}"
                </div>
              ) : (
                <p className="text-xs font-normal italic text-white/45">
                  El conductor no registró ningún comentario para este evento.
                </p>
              )}
            </div>

            {/* Trazabilidad y Nota de Privacidad */}
            <div className={`p-6 text-xs font-normal text-white/60 ${GLASS_CARD}`}>
              <h4 className="mb-3 text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55">
                Metadatos de trazabilidad
              </h4>
              <ul className="space-y-1.5 font-mono text-white/50">
                <li><span className="text-white/70">ID del Evento:</span> {event.id}</li>
                <li><span className="text-white/70">ID de Sesión:</span> {event.sesion_id}</li>
                <li><span className="text-white/70">ID Tipo Incidente:</span> {event.tipo_incidente_id}</li>
              </ul>
              <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.05] p-4 text-white/65">
                <strong className="font-semibold text-white/85">Nota de Protección de Datos:</strong> Conforme a la Ley 1581 de 2012, este sistema registra únicamente metadatos métricos y temporales. No se almacenan ni transmiten imágenes o grabaciones de video del conductor.
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
