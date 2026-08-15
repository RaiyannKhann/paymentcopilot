"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { List, X } from "@phosphor-icons/react/dist/ssr";
import { AmbientBackdrop } from "./AmbientBackdrop";
import { BrandMark } from "./BrandMark";
import { DisclaimerBanner } from "./DisclaimerBanner";
import { SIDEBAR_LINKS, Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // The drawer closes on navigation via Sidebar's onNavigate, on backdrop click, and
  // on Escape here — a drawer left open over new content is the classic mobile trap.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  const current =
    SIDEBAR_LINKS.find((link) =>
      link.href === "/" ? pathname === "/" : pathname.startsWith(link.href)
    ) ?? SIDEBAR_LINKS[0];

  return (
    <>
      <AmbientBackdrop />

      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-violet focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-on-violet"
      >
        Skip to content
      </a>

      {/* Desktop rail */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[17rem] border-r border-white/8 bg-canvas-deep/70 backdrop-blur-xl lg:block">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 cursor-default bg-canvas-deep/80 backdrop-blur-sm"
          />
          <div className="absolute inset-y-0 left-0 w-[17rem] max-w-[85vw] border-r border-white/10 bg-canvas-deep shadow-2xl">
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className="lg:pl-[17rem]">
        <DisclaimerBanner />

        {/* Mobile top bar */}
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-white/8 bg-canvas/80 px-4 py-3 backdrop-blur-xl lg:hidden">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
            aria-expanded={drawerOpen}
            className="inline-flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl border border-white/10 text-ink-muted transition-colors hover:bg-white/5 hover:text-ink"
          >
            {drawerOpen ? <X size={18} weight="bold" /> : <List size={18} weight="bold" />}
          </button>
          <BrandMark size={28} />
          <span className="truncate text-sm font-semibold text-ink">{current.label}</span>
        </header>

        <main id="main" className="min-h-dvh">
          {children}
        </main>
      </div>
    </>
  );
}
