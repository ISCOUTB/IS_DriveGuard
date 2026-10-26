import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Car,
  Clock,
  Gauge,
  MessageSquare,
  ShieldCheck,
  User,
} from "lucide-react";
import AmbientBackground from "../components/AmbientBackground";
import Navbar from "../components/Navbar";
import SideRail from "../components/SideRail";
import {
  formatearFecha,
  getCurrentUser,
  getEventoDetallado,
  updateEvento,
} from "../services/api";

const labelClass =
  "text-[9.5px] font-semibold uppercase tracking-[0.13em] text-ink-muted";

const severityBadge = {
  alta: "badge badge-alta",
  media: "badge badge-media",
  baja: "badge badge-baja",
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
    <div className="relative min-h-screen text-ink">
      <AmbientBackground />

      <div className="relative z-10 mx-auto w-full max-w-[1500px] px-4 pb-10 pt-4 sm:px-6 lg:pl-[104px] lg:pr-8">
        <Navbar />
        <SideRail active="detail" />

        <main className="relative mx-auto mt-7 max-w-5xl sm:mt-9">
          <Link
            to="/dashboard"
            className="glass-chip reveal mb-5 px-3.5 py-2 text-[11px] transition hover:bg-white/50"
          >
            <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.9} />
            <span>Volver al panel de incidentes</span>
          </Link>

          {loading ? (
            <div className="glass-panel p-12 text-center">
              <div className="mx-auto mb-3 h-9 w-9 animate-spin rounded-full border-2 border-white/50 border-t-drive-teal" />
              <p className="text-sm text-ink-muted">Cargando detalle del incidente...</p>
            </div>
          ) : error ? (
            <div className="glass-panel flex flex-col items-center gap-3 p-10 text-center">
              <span className="icon-chip h-11 w-11 text-[#a85448]">
                <AlertTriangle className="h-5 w-5" strokeWidth={1.8} />
              </span>
              <p className="font-semibold text-[#8f4439]">{error}</p>
            </div>
          ) : event ? (
            <div className="space-y-4">
              {/* Encabezado del Incidente */}
              <section className="glass-panel reveal relative overflow-hidden p-6 sm:p-7">
                <ShieldCheck
                  className="pointer-events-none absolute -bottom-14 -right-6 h-52 w-52 text-[#8d7862]/[0.08]"
                  strokeWidth={0.7}
                />
                <span className="pointer-events-none absolute -right-20 -top-24 h-56 w-56 rounded-full border border-white/25" />

                <div className="relative flex flex-col justify-between gap-6 md:flex-row md:items-center">
                  <div>
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h1 className="text-[1.75rem] font-semibold leading-tight tracking-[-0.035em] text-ink sm:text-[2rem]">
                        {event.tipo_incidente_etiqueta || event.tipo_incidente_nombre}
                      </h1>
                      <span className={severityBadge[event.severidad] ?? "badge badge-neutral"}>
                        Severidad {event.severidad}
                      </span>
                      {event.revisado ? (
                        <span className="glass-chip">
                          <span className="status-dot status-dot--done" />
                          Revisado
                        </span>
                      ) : (
                        <span className="glass-chip">
                          <span className="status-dot status-dot--pending" />
                          Pendiente de revisión
                        </span>
                      )}
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11.5px] font-normal text-ink-muted">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-ink-soft" strokeWidth={1.8} />
                        Ocurrencia:{" "}
                        <strong className="font-semibold text-ink-soft">
                          {formatearFecha(event.fecha_hora)}
                        </strong>
                      </span>
                      <span className="h-1 w-1 rounded-full bg-ink-muted/40" />
                      <span>
                        Sincronizado:{" "}
                        <strong className="font-semibold text-ink-soft">
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
                      className={`btn ${event.revisado ? "btn-glass" : "btn-teal"} flex-none`}
                    >
                      <ShieldCheck className="h-4 w-4" strokeWidth={1.9} />
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
              </section>

              {/* Métricas Clave */}
              <div className="reveal reveal-delay-1 grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  { icon: Clock, label: "Duración", value: event.duracion_segundos, unit: "segundos", mono: false },
                  { icon: Gauge, label: "Métrica calculada", value: event.valor_metrica, unit: null, mono: true, accent: true },
                  { icon: User, label: "Conductor", value: event.conductor_nombre, unit: null, mono: false, small: true },
                  { icon: Car, label: "Vehículo asignado", value: event.vehiculo_placa, unit: null, mono: false, small: true },
                ].map(({ icon: Icon, label, value, unit, mono, small, accent }) => (
                  <div
                    key={label}
                    className={
                      accent
                        ? "relative overflow-hidden rounded-[24px] border border-white/35 bg-gradient-to-br from-[#1aab8c] via-[#0d8b74] to-[#07705d] p-5 text-white shadow-[0_28px_55px_-30px_rgba(5,83,68,0.7),inset_0_1px_0_rgba(255,255,255,0.4)]"
                        : "glass-soft p-5"
                    }
                  >
                    {accent && (
                      <span className="pointer-events-none absolute -right-10 -top-14 h-36 w-36 rounded-full border border-white/15" />
                    )}
                    <div className="relative flex items-center gap-2.5">
                      <span
                        className={
                          accent
                            ? "inline-grid h-8 w-8 place-items-center rounded-full border border-white/25 bg-white/15 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.3)]"
                            : "icon-chip h-8 w-8"
                        }
                      >
                        <Icon className="h-3.5 w-3.5" strokeWidth={1.8} />
                      </span>
                      <span className={accent ? "text-[9.5px] font-semibold uppercase tracking-[0.13em] text-white/70" : labelClass}>
                        {label}
                      </span>
                    </div>
                    <p
                      className={`relative mt-3 font-semibold tracking-[-0.02em] ${
                        accent ? "text-white" : "text-ink"
                      } ${small ? "text-[17px]" : "text-[1.45rem]"} ${
                        mono ? "font-mono" : "tabular-nums"
                      }`}
                    >
                      {value}
                      {unit && (
                        <span className={`ml-1.5 text-[11px] font-normal ${accent ? "text-white/60" : "text-ink-muted"}`}>
                          {unit}
                        </span>
                      )}
                    </p>
                  </div>
                ))}
              </div>

              {/* Comentario del Conductor */}
              <section className="glass-panel reveal reveal-delay-2 p-6">
                <h3 className="mb-3.5 flex items-center gap-2.5 text-[14px] font-semibold tracking-[-0.015em] text-ink">
                  <span className="icon-chip h-8 w-8">
                    <MessageSquare className="h-3.5 w-3.5" strokeWidth={1.8} />
                  </span>
                  <span>Comentario registrado por el conductor</span>
                </h3>
                {event.comentario_conductor ? (
                  <blockquote className="glass-soft relative p-4 text-[12.5px] font-normal italic leading-relaxed text-ink-soft">
                    <span className="pointer-events-none absolute left-3 top-1 select-none font-serif text-3xl leading-none text-ink/10">
                      “
                    </span>
                    <span className="relative pl-4">{event.comentario_conductor}</span>
                  </blockquote>
                ) : (
                  <p className="text-[11.5px] font-normal italic text-ink-muted">
                    El conductor no registró ningún comentario para este evento.
                  </p>
                )}
              </section>

              {/* Trazabilidad y Nota de Privacidad */}
              <section className="glass-panel reveal reveal-delay-3 p-6">
                <h4 className={labelClass}>Metadatos de trazabilidad</h4>
                <ul className="mt-3 grid gap-2 font-mono text-[11px] text-ink-muted sm:grid-cols-3">
                  <li className="glass-soft px-3.5 py-2.5">
                    <span className="block text-[9px] font-semibold uppercase tracking-[0.1em] text-ink-muted/75">
                      ID del Evento
                    </span>
                    {event.id}
                  </li>
                  <li className="glass-soft px-3.5 py-2.5">
                    <span className="block text-[9px] font-semibold uppercase tracking-[0.1em] text-ink-muted/75">
                      ID de Sesión
                    </span>
                    {event.sesion_id}
                  </li>
                  <li className="glass-soft px-3.5 py-2.5">
                    <span className="block text-[9px] font-semibold uppercase tracking-[0.1em] text-ink-muted/75">
                      ID Tipo Incidente
                    </span>
                    {event.tipo_incidente_id}
                  </li>
                </ul>

                <div className="mt-3.5 rounded-2xl border border-white/45 bg-white/20 p-4 text-[11.5px] font-normal leading-relaxed text-ink-soft backdrop-blur-md">
                  <strong className="font-semibold text-ink">Nota de Protección de Datos:</strong>{" "}
                  Conforme a la Ley 1581 de 2012, este sistema registra únicamente metadatos métricos y
                  temporales. No se almacenan ni transmiten imágenes o grabaciones de video del
                  conductor.
                </div>
              </section>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}
