import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert, Lock, Mail, ArrowRight } from "lucide-react";
import { login } from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [correo, setCorreo] = useState("supervisor@flota.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(correo, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-950 p-4">
      {/* Orbes de color para que el cristal tenga contenido que desenfocar */}
      <div className="absolute -top-32 -left-24 h-[28rem] w-[28rem] rounded-full bg-amber-500/50 blur-[90px]" />
      <div className="absolute top-1/3 -right-32 h-[24rem] w-[24rem] rounded-full bg-fuchsia-500/40 blur-[90px]" />
      <div className="absolute -bottom-32 left-1/4 h-[26rem] w-[26rem] rounded-full bg-sky-500/45 blur-[90px]" />

      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-300/30 to-amber-600/10 backdrop-blur-xl border border-white/20 shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_0_0_rgba(255,255,255,0.3)]">
            <ShieldAlert className="h-7 w-7 text-amber-200 drop-shadow-[0_0_8px_rgba(251,191,36,0.6)]" strokeWidth={1.75} />
          </div>
          <h1 className="font-[system-ui] text-[2rem] font-semibold tracking-[-0.02em] text-white drop-shadow-md">DriveGuard</h1>
          <p className="mt-1.5 text-[0.8125rem] font-normal tracking-wide text-white/60">
            Detección de fatiga y supervisión en tiempo real
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="relative overflow-hidden rounded-[2rem] border border-white/20 bg-gradient-to-br from-white/25 via-white/10 to-white/5 p-8 shadow-[0_8px_40px_0_rgba(0,0,0,0.35),inset_0_1px_1px_0_rgba(255,255,255,0.35),inset_0_-1px_1px_0_rgba(255,255,255,0.08)] backdrop-blur-3xl ring-1 ring-inset ring-white/10"
        >
          <h2 className="mb-6 text-[1.0625rem] font-semibold tracking-[-0.01em] text-white/95">Iniciar sesión</h2>

          {error && (
            <div className="mb-5 rounded-xl border border-red-500/30 bg-red-500/15 p-3 text-xs font-medium text-red-200 backdrop-blur-md">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label className="mb-1.5 block text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55">
              Correo electrónico
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-amber-200/70">
                <Mail className="h-4 w-4" strokeWidth={1.75} />
              </div>
              <input
                type="email"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-sm text-white placeholder-slate-400 shadow-inner backdrop-blur-md focus:border-amber-400/50 focus:bg-white/10 focus:outline-none focus:ring-2 focus:ring-amber-400/30 transition-all"
                placeholder="supervisor@flota.com"
                required
              />
            </div>
          </div>

          <div className="mb-6">
            <label className="mb-1.5 block text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55">
              Contraseña
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-amber-200/70">
                <Lock className="h-4 w-4" strokeWidth={1.75} />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-sm text-white placeholder-slate-400 shadow-inner backdrop-blur-md focus:border-amber-400/50 focus:bg-white/10 focus:outline-none focus:ring-2 focus:ring-amber-400/30 transition-all"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-amber-500/90 py-3 text-sm font-semibold text-slate-950 shadow-[0_4px_20px_0_rgba(245,158,11,0.4)] backdrop-blur-md transition-all hover:bg-amber-400 hover:shadow-[0_4px_25px_0_rgba(245,158,11,0.6)] focus:outline-none disabled:opacity-50"
          >
            {loading ? (
              <span>Ingresando...</span>
            ) : (
              <>
                <span>Ingresar al panel</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
