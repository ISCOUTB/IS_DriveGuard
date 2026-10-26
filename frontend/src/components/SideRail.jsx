import {
  ArrowUp,
  LayoutDashboard,
  ListFilter,
  RefreshCw,
  ShieldAlert,
  SlidersHorizontal,
} from "lucide-react";
import { Link } from "react-router-dom";

function RailAction({ label, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className="rail-button"
    >
      {children}
    </button>
  );
}

export default function SideRail({
  active = "dashboard",
  onRefresh,
  onFilter,
  onTable,
  refreshing = false,
}) {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <aside className="side-rail" aria-label="Navegación rápida">
      <Link to="/dashboard" className="rail-brand" title="DriveGuard" aria-label="DriveGuard">
        <ShieldAlert className="h-5 w-5" strokeWidth={1.8} />
      </Link>

      <span className="rail-rule" />

      <nav className="flex flex-1 flex-col items-center gap-1.5" aria-label="Secciones">
        <Link
          to="/dashboard"
          title="Panel de incidentes"
          aria-label="Panel de incidentes"
          className={`rail-button ${active === "dashboard" ? "rail-button-active" : ""}`}
        >
          <LayoutDashboard className="h-[18px] w-[18px]" strokeWidth={1.7} />
        </Link>

        {onFilter && (
          <RailAction label="Ir a los filtros" onClick={onFilter}>
            <SlidersHorizontal className="h-[18px] w-[18px]" strokeWidth={1.7} />
          </RailAction>
        )}

        {onTable && (
          <RailAction label="Ir al listado de incidentes" onClick={onTable}>
            <ListFilter className="h-[18px] w-[18px]" strokeWidth={1.7} />
          </RailAction>
        )}

        {onRefresh && (
          <RailAction label="Actualizar datos" onClick={onRefresh}>
            <RefreshCw
              className={`h-[18px] w-[18px] ${refreshing ? "animate-spin" : ""}`}
              strokeWidth={1.7}
            />
          </RailAction>
        )}
      </nav>

      <span className="rail-rule" />

      <RailAction label="Volver arriba" onClick={scrollToTop}>
        <ArrowUp className="h-[18px] w-[18px]" strokeWidth={1.7} />
      </RailAction>
    </aside>
  );
}
