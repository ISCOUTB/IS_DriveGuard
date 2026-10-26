import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert, Lock, Mail, ArrowRight } from "lucide-react";
import AmbientBackground from "../components/AmbientBackground";
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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10 text-ink">
      <AmbientBackground />

      <div className="relative z-10 w-full max-w-[430px]">
        <div className="reveal mb-7 text-center">
          <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] border border-white/50 bg-gradient-to-br from-[#1cae90] via-[#0d8a73] to-[#076756] text-white shadow-[0_18px_36px_-18px_rgba(6,84,69,0.85),inset_0_1px_0_rgba(255,255,255,0.45)]">
            <span className="pointer-events-none absolute inset-0 rounded-[22px] bg-[radial-gradient(80%_60%_at_30%_0%,rgba(255,255,255,0.4),transparent_65%)]" />
            <ShieldAlert className="relative h-8 w-8" strokeWidth={1.7} />
          </div>
          <h1 className="mt-5 text-[2rem] font-semibold leading-none tracking-[-0.04em] text-ink">
            DriveGuard
          </h1>
          <p className="mt-2.5 text-[12.5px] font-normal tracking-[0.005em] text-ink-muted">
            Detección de fatiga y supervisión en tiempo real
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="glass-panel reveal reveal-delay-1 relative overflow-hidden p-6 sm:p-8"
        >
          <span className="pointer-events-none absolute -right-16 -top-20 h-52 w-52 rounded-full border border-white/30" />
          <span className="pointer-events-none absolute -bottom-24 -left-16 h-56 w-56 rounded-full border border-white/20" />

          <div className="relative">
            <h2 className="mb-6 text-[16px] font-semibold tracking-[-0.02em] text-ink">
              Iniciar sesión
            </h2>

            {error && (
              <div className="mb-5 rounded-2xl border border-[#c1685d]/30 bg-[#c1685d]/10 p-3.5 text-[11.5px] font-medium text-[#8f4439] backdrop-blur-md">
                {error}
              </div>
            )}

            <div className="mb-4">
              <label className="filter-label mb-2">Correo electrónico</label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-ink-muted">
                  <Mail className="h-4 w-4" strokeWidth={1.8} />
                </div>
                <input
                  type="email"
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                  className="field-input"
                  placeholder="supervisor@flota.com"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="filter-label mb-2">Contraseña</label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-ink-muted">
                  <Lock className="h-4 w-4" strokeWidth={1.8} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="field-input"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-teal min-h-[48px] w-full text-[13px]"
            >
              {loading ? (
                <span>Ingresando...</span>
              ) : (
                <>
                  <span>Ingresar al panel</span>
                  <ArrowRight className="h-4 w-4" strokeWidth={1.9} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
