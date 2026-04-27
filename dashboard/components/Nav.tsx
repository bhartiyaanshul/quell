"use client";

import { Activity, LayoutDashboard, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/", label: "Incidents", icon: LayoutDashboard },
  { href: "/stats", label: "Stats", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg-base/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
        <div className="flex items-center gap-3">
          <motion.div
            className="h-7 w-7 rounded-lg bg-gradient-to-br from-accent-hi via-accent to-cool-deep"
            animate={{ rotate: [0, 3, 0, -3, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          />
          <div>
            <div className="text-sm font-semibold tracking-tight">Quell</div>
            <div className="text-[11px] text-fg-dim">local dashboard</div>
          </div>
        </div>
        <nav className="flex items-center gap-1">
          {LINKS.map((l) => {
            const active =
              l.href === "/"
                ? pathname === "/" || pathname?.startsWith("/incidents")
                : pathname?.startsWith(l.href);
            const Icon = l.icon;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "relative flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition",
                  active
                    ? "text-fg"
                    : "text-fg-muted hover:bg-bg-raised/60 hover:text-fg",
                )}
              >
                <Icon size={14} />
                <span>{l.label}</span>
                {active && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-x-2 -bottom-[9px] h-0.5 rounded-full bg-accent shadow-[0_0_10px_rgba(251,146,60,0.7)]"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
