// A router glyph — one input fanning out to three branches — rather than a generic
// sparkle. Routing is what this product actually does (UC1/UC2/UC3).
export function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <span
      className="relative inline-flex shrink-0 items-center justify-center rounded-[10px] border border-white/15"
      style={{
        width: size,
        height: size,
        background: "linear-gradient(145deg, #a78bfa 0%, #7c3aed 45%, #4c1d95 100%)",
        boxShadow: "0 6px 18px -6px rgba(139,92,246,0.75), inset 0 1px 0 rgba(255,255,255,0.35)",
      }}
    >
      <svg
        width={size * 0.6}
        height={size * 0.6}
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        stroke="#ffffff"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M3 12h4" />
        <path d="M7 12c5 0 5-7 10-7" />
        <path d="M7 12h10" />
        <path d="M7 12c5 0 5 7 10 7" />
        <circle cx="19" cy="5" r="2" fill="#ffffff" stroke="none" />
        <circle cx="19" cy="12" r="2" fill="#ffffff" stroke="none" />
        <circle cx="19" cy="19" r="2" fill="#ffffff" stroke="none" />
      </svg>
    </span>
  );
}
