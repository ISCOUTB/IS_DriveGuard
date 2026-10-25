import { LogOut, ShieldAlert, User } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { getCurrentUser, logout } from "../services/api";

export default function Navbar() {
  const navigate = useNavigate();
  const user = getCurrentUser();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-white/[0.06] px-6 py-3.5 text-white shadow-[0_8px_32px_0_rgba(0,0,0,0.3),inset_0_-1px_0_0_rgba(255,255,255,0.05)] backdrop-blur-3xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-3 transition hover:opacity-90">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-gradient-to-br from-amber-300/30 to-amber-600/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.3)]">
            <ShieldAlert className="h-5 w-5 text-amber-200 drop-shadow-[0_0_6px_rgba(251,191,36,0.5)]" strokeWidth={1.75} />
          </div>
          <div className="flex items-center gap-2.5">
            <span className="text-base font-semibold tracking-[-0.01em] text-white">DriveGuard</span>
            <span className="rounded-full border border-white/15 bg-white/10 px-2.5 py-0.5 text-[0.6875rem] font-medium tracking-wide text-white/65">
              Supervisión
            </span>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          {user && (
            <div className="hidden items-center gap-2 rounded-xl border border-white/15 bg-white/10 px-3 py-1.5 text-xs sm:flex">
              <User className="h-3.5 w-3.5 text-amber-200/70" strokeWidth={1.75} />
              <span className="font-medium text-white/90">{user.nombre_completo}</span>
              <span className="text-white/30">•</span>
              <span className="capitalize text-white/55">{user.rol}</span>
            </div>
          )}

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-2 rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs font-medium text-white/80 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.2)] transition hover:bg-white/20 hover:text-white"
          >
            <LogOut className="h-3.5 w-3.5" strokeWidth={1.75} />
            <span>Cerrar sesión</span>
          </button>
        </div>
      </div>
    </header>
  );
}
