export default function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-950">
      <div className="absolute -top-32 -left-24 h-[28rem] w-[28rem] rounded-full bg-amber-500/40 blur-[100px]" />
      <div className="absolute top-1/3 -right-32 h-[24rem] w-[24rem] rounded-full bg-fuchsia-500/30 blur-[100px]" />
      <div className="absolute -bottom-32 left-1/4 h-[26rem] w-[26rem] rounded-full bg-sky-500/35 blur-[100px]" />
    </div>
  );
}
