"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, Github, Menu, X } from "lucide-react";
import Image from "next/image";

import { REPO_URL } from "@/lib/constants";

const NAV_LINKS: { label: string; href: string; hint: string }[] = [
  { label: "Watch it work", href: "#watch", hint: "Live terminal demo" },
  { label: "How it works", href: "#how-it-works", hint: "4-stage pipeline" },
  { label: "Features", href: "#features", hint: "9 capabilities" },
  { label: "Skills", href: "#skills", hint: "19 runbooks" },
  { label: "Install", href: "#install", hint: "5 ways to install" },
  { label: "Architecture", href: "#architecture", hint: "Under the hood" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Drive the bg fade with a class toggle, not framer-motion's `useScroll`.
  // useScroll/useTransform re-renders the header on every scroll event;
  // this listener sets state only when crossing the threshold.
  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close on escape, lock body scroll while drawer is open.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <>
      <header
        className={
          "fixed inset-x-0 top-0 z-50 transition-colors duration-300 " +
          (scrolled
            ? "bg-bg-base/70 backdrop-blur-md"
            : "bg-transparent backdrop-blur-0")
        }
      >
        {/* 3-column grid keeps the wordmark perfectly centred regardless of
            the left/right pill widths. `justify-between` on a flex row drifts
            the centre item whenever the two ends aren't equal width. */}
        <nav className="mx-auto grid max-w-6xl grid-cols-[1fr_auto_1fr] items-center gap-3 px-5 py-4">
          {/* Left — Menu */}
          <div className="flex justify-start">
            <button
              type="button"
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
              className="group relative inline-flex h-9 items-center gap-2 rounded-full border border-border bg-bg-raised/80 pl-3 pr-3.5 text-xs font-medium text-fg-muted backdrop-blur-md transition hover:border-border-bright hover:text-fg sm:text-sm"
            >
              <span className="relative grid h-4 w-4 place-items-center">
                <AnimatePresence initial={false} mode="wait">
                  {open ? (
                    <motion.span
                      key="x"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.18 }}
                      className="absolute inset-0 grid place-items-center"
                    >
                      <X size={14} />
                    </motion.span>
                  ) : (
                    <motion.span
                      key="m"
                      initial={false}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: -90, opacity: 0 }}
                      transition={{ duration: 0.18 }}
                      className="absolute inset-0 grid place-items-center"
                    >
                      <Menu size={14} />
                    </motion.span>
                  )}
                </AnimatePresence>
              </span>
              <span>{open ? "Close" : "Menu"}</span>
            </button>
          </div>

          {/* Centre — wordmark, perfectly centred via grid auto column. */}
          <a
            href="#top"
            className="group flex items-center justify-center gap-2 text-fg"
            aria-label="Quell home"
          >
            <Image
              src="/logo.svg"
              alt=""
              width={22}
              height={22}
              priority
              className="transition-transform duration-500 group-hover:rotate-12"
            />
            <span className="text-xs font-semibold uppercase tracking-[0.32em] sm:text-sm">
              Quell
            </span>
          </a>

          {/* Right — pill group */}
          <div className="flex items-center justify-end gap-2">
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden h-9 items-center gap-1.5 rounded-full border border-border bg-bg-raised/80 px-3 text-xs font-medium text-fg-muted backdrop-blur-md transition hover:border-border-bright hover:text-fg sm:inline-flex sm:text-sm"
            >
              <Github size={13} />
              <span>GitHub</span>
            </a>
            <a
              href="#install"
              className="inline-flex h-9 items-center rounded-full bg-accent px-3.5 text-xs font-semibold text-bg-base shadow-[0_8px_24px_-8px_rgba(251,146,60,0.55)] transition hover:shadow-[0_12px_30px_-8px_rgba(251,146,60,0.75)] sm:text-sm"
            >
              Install
            </a>
          </div>
        </nav>
      </header>

      {/* Drawer overlay + panel */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              key="scrim"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              onClick={() => setOpen(false)}
              className="fixed inset-0 z-40 bg-bg-base/55 backdrop-blur-sm"
              aria-hidden
            />

            <motion.div
              key="panel"
              initial={{ y: -16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -16, opacity: 0 }}
              transition={{
                duration: 0.32,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="fixed inset-x-0 top-[68px] z-50 px-4 sm:px-5"
              role="dialog"
              aria-modal="true"
              aria-label="Site navigation"
            >
              <div className="mx-auto max-w-2xl overflow-hidden rounded-3xl border border-border bg-bg-raised/85 shadow-[0_30px_120px_-30px_rgba(0,0,0,0.8)] backdrop-blur-2xl">
                {/* Section list */}
                <div className="grid grid-cols-1 gap-px bg-border/40 sm:grid-cols-2">
                  {NAV_LINKS.map((link, i) => (
                    <motion.a
                      key={link.href}
                      href={link.href}
                      onClick={() => setOpen(false)}
                      initial={{ y: 10, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      transition={{
                        delay: 0.08 + i * 0.03,
                        duration: 0.4,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                      className="group flex items-center justify-between gap-4 bg-bg-raised/85 p-5 transition hover:bg-bg-base/70"
                    >
                      <div className="min-w-0">
                        <div className="text-base font-semibold text-fg">
                          {link.label}
                        </div>
                        <div className="mt-0.5 text-xs text-fg-dim">
                          {link.hint}
                        </div>
                      </div>
                      <ArrowUpRight
                        size={16}
                        className="shrink-0 text-fg-dim transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-accent"
                      />
                    </motion.a>
                  ))}
                </div>

                {/* Footer row inside drawer */}
                <div className="flex items-center justify-between gap-3 border-t border-border/60 bg-bg-base/40 px-5 py-4">
                  <a
                    href={REPO_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/70 px-3.5 py-1.5 text-xs font-medium text-fg-muted transition hover:border-border-bright hover:text-fg"
                  >
                    <Github size={13} />
                    <span>View on GitHub</span>
                  </a>
                  <span className="font-mono text-[10px] text-fg-dim">
                    esc to close
                  </span>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
