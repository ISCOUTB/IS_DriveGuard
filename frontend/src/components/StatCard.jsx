import { ShieldAlert } from "lucide-react";

const variantClass = {
  hero: "stat-card-hero glass-panel",
  light: "stat-card-light",
  teal: "stat-card-teal",
};

const dotClass = {
  default: "stat-dot",
  rose: "stat-dot stat-dot-rose",
  amber: "stat-dot stat-dot-amber",
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  variant = "light",
  accent = "default",
  actions = null,
  className = "",
}) {
  const isTeal = variant === "teal";

  return (
    <article className={`stat-card ${variantClass[variant] ?? variantClass.light} ${className}`}>
      {variant === "hero" && (
        <>
          <ShieldAlert
            className="pointer-events-none absolute -bottom-12 -right-8 h-56 w-56 text-[#8d7862]/[0.09]"
            strokeWidth={0.7}
          />
          <span className="pointer-events-none absolute -right-24 -top-28 h-64 w-64 rounded-full border border-white/30" />
          <span className="pointer-events-none absolute -right-12 -top-16 h-44 w-44 rounded-full border border-white/25" />
          <span className="pointer-events-none absolute bottom-5 right-6 h-2.5 w-2.5 rounded-full bg-white/60 shadow-[0_0_0_5px_rgba(255,255,255,0.14)]" />
        </>
      )}

      {isTeal && (
        <>
          <span className="pointer-events-none absolute -right-12 -top-20 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
          <span className="pointer-events-none absolute -bottom-28 -left-12 h-56 w-56 rounded-full border border-white/15" />
          <span className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full border border-white/15" />
        </>
      )}

      <div className="relative z-10 flex h-full w-full flex-col">
        <div className="flex items-start justify-between gap-4">
          <p className="stat-label">{title}</p>
          {icon && <span className="stat-icon">{icon}</span>}
        </div>

        <p className="stat-value">{value}</p>

        {subtitle && (
          <p className="stat-sub">
            <span className={isTeal ? "stat-dot" : dotClass[accent] ?? dotClass.default} />
            <span>{subtitle}</span>
          </p>
        )}

        {actions && <div className="mt-auto flex flex-wrap items-center gap-2.5 pt-7">{actions}</div>}
      </div>
    </article>
  );
}
