interface OrbProps {
  /** Drives the halo: idle while waiting for input, pulsing while a query is in flight. */
  active?: boolean;
  size?: number;
}

// The hero sphere: a CSS-only lit ball (offset highlight + rim light + cast glow).
// No image, no canvas, no animation library.
export function Orb({ active = false, size = 96 }: OrbProps) {
  return (
    <span
      className="relative inline-grid place-items-center"
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      {active && (
        <>
          <span
            className="absolute inset-0 rounded-full border border-violet-bright/50"
            style={{ animation: "pulse-ring 1.8s var(--ease-out-soft) infinite" }}
          />
          <span
            className="absolute inset-0 rounded-full border border-violet-bright/40"
            style={{ animation: "pulse-ring 1.8s var(--ease-out-soft) 0.6s infinite" }}
          />
        </>
      )}

      <span
        className={active ? "" : "animate-drift"}
        style={{
          width: size,
          height: size,
          borderRadius: "9999px",
          background:
            "radial-gradient(circle at 32% 28%, #e9d5ff 0%, #a78bfa 22%, #7c3aed 52%, #3b0f78 82%, #1b0740 100%)",
          boxShadow:
            "0 0 60px -8px rgba(139,92,246,0.65), 0 0 140px -20px rgba(124,58,237,0.5), inset -8px -10px 28px rgba(20,4,50,0.75), inset 6px 8px 22px rgba(233,213,255,0.35)",
        }}
      />
    </span>
  );
}
