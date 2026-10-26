import { LayoutDashboard, LogOut } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { getCurrentUser, logout } from "../services/api";

function getInitials(name) {
  if (!name) return "";
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

export default function Navbar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const user = getCurrentUser();
  const isDashboard = pathname === "/dashboard";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="glass-nav sticky top-4 z-30 flex h-16 items-center gap-2 px-3 sm:px-4">
      <Link
        to="/dashboard"
        className="flex min-w-0 items-center gap-3 rounded-full transition hover:opacity-95"
      >
        <span className="avatar-ring">
          <span className="avatar-inner">{getInitials(user?.nombre_completo) || "DG"}</span>
        </span>
        <span className="min-w-0 pr-1">
          <span className="block max-w-[54vw] truncate text-[12.5px] font-semibold tracking-[-0.015em] text-ink sm:max-w-[300px]">
            {user ? `Bienvenido, ${user.nombre_completo}` : "Bienvenido a DriveGuard"}
          </span>
          <span className="mt-1 flex items-center gap-1.5 text-[10px] font-medium text-ink-muted">
            <span className="h-1.5 w-1.5 flex-none rounded-full bg-drive-teal shadow-[0_0_0_3px_rgba(15,144,119,0.13)]" />
            <span className="truncate">
              DriveGuard · {user?.rol ?? "Supervisión"}
            </span>
          </span>
        </span>
      </Link>

      <div className="mx-auto hidden md:block">
        <Link
          to="/dashboard"
          className={`nav-pill ${isDashboard ? "nav-pill-active" : ""}`}
        >
          <LayoutDashboard className="h-3.5 w-3.5" strokeWidth={1.8} />
          <span>Panel de incidentes</span>
        </Link>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          onClick={handleLogout}
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
          className="icon-button"
        >
          <LogOut className="h-4 w-4" strokeWidth={1.8} />
        </button>
      </div>
    </header>
  );
}
