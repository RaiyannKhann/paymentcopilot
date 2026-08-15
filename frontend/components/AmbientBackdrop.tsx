// Fixed, non-interactive atmosphere behind the whole app: a violet key light from the
// top, a cooler indigo fill from the lower left, and a faint grid that gives the glass
// panels something to refract. Pure CSS — no images, no layout cost.
export function AmbientBackdrop() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-canvas" />

      <div
        className="absolute -top-[28rem] left-1/2 h-[52rem] w-[68rem] -translate-x-1/2 rounded-full opacity-70 blur-3xl"
        style={{
          background:
            "radial-gradient(closest-side, rgba(139,92,246,0.32), rgba(76,29,149,0.14) 55%, transparent 100%)",
        }}
      />

      <div
        className="absolute -bottom-64 -left-40 h-[36rem] w-[36rem] rounded-full opacity-60 blur-3xl"
        style={{
          background:
            "radial-gradient(closest-side, rgba(67,56,202,0.28), rgba(67,56,202,0.08) 55%, transparent 100%)",
        }}
      />

      <div
        className="absolute inset-0 opacity-[0.055]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "radial-gradient(ellipse 90% 65% at 50% 0%, #000 20%, transparent 78%)",
          WebkitMaskImage: "radial-gradient(ellipse 90% 65% at 50% 0%, #000 20%, transparent 78%)",
        }}
      />

      {/* Bottom vignette — keeps long pages from fading into flat black at the fold. */}
      <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-canvas-deep to-transparent" />
    </div>
  );
}
