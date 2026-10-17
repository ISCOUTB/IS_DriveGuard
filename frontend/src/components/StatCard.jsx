export default function StatCard({ title, value, subtitle, icon }) {
  return (
    <div className="rounded-3xl border border-white/15 bg-gradient-to-br from-white/15 via-white/5 to-white/[0.02] p-5 shadow-[0_8px_40px_0_rgba(0,0,0,0.35),inset_0_1px_1px_0_rgba(255,255,255,0.25)] backdrop-blur-3xl">
      <div className="flex items-center justify-between">
        <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-white/55">{title}</p>
        {icon && (
          <div className="rounded-xl border border-white/20 bg-white/10 p-2 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.3)]">
            {icon}
          </div>
        )}
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-[-0.02em] text-white">{value}</p>
      {subtitle && <p className="mt-1 text-xs font-normal text-white/50">{subtitle}</p>}
    </div>
  );
}
