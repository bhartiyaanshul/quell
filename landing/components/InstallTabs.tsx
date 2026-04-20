"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { SectionHeader } from "@/components/SectionHeader";
import { INSTALL_COMMANDS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function InstallTabs() {
  const [active, setActive] = useState<string>(INSTALL_COMMANDS[0].id);
  const [copied, setCopied] = useState(false);

  const current =
    INSTALL_COMMANDS.find((c) => c.id === active) ?? INSTALL_COMMANDS[0];

  async function copy() {
    try {
      await navigator.clipboard.writeText(current.command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      // no-op
    }
  }

  return (
    <section
      id="install"
      className="relative mx-auto max-w-5xl px-6 py-24 sm:py-28"
    >
      <SectionHeader
        eyebrow="Install in 10 seconds"
        title={
          <>
            Five ways to get{" "}
            <span className="text-gradient">Quell on your PATH.</span>
          </>
        }
        body="Pick whatever matches your environment. All five channels install the same binary."
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative mt-14"
      >
        {/* Outer glow */}
        <div
          aria-hidden
          className="absolute -inset-5 -z-10 rounded-3xl bg-gradient-to-br from-accent/20 to-cool/20 opacity-40 blur-2xl"
        />

        <div className="overflow-hidden rounded-2xl border border-border bg-bg-raised/60 backdrop-blur">
          {/* Tab bar */}
          <div
            role="tablist"
            aria-label="Install method"
            className="flex overflow-x-auto border-b border-border bg-bg-subtle/60 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {INSTALL_COMMANDS.map((c) => {
              const isActive = active === c.id;
              return (
                <button
                  key={c.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActive(c.id)}
                  className={cn(
                    "relative flex-shrink-0 px-5 py-4 text-left text-sm font-medium transition",
                    isActive ? "text-fg" : "text-fg-muted hover:text-fg",
                  )}
                >
                  <span className="block">{c.label}</span>
                  <span className="mt-0.5 block text-[11px] font-normal text-fg-dim">
                    {c.sublabel}
                  </span>
                  {isActive && (
                    <motion.span
                      layoutId="install-tab-underline"
                      className="absolute inset-x-3 bottom-0 h-0.5 rounded-full bg-accent shadow-[0_0_12px_rgba(251,146,60,0.8)]"
                      transition={{
                        type: "spring",
                        stiffness: 380,
                        damping: 30,
                      }}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Command panel */}
          <div className="relative p-6 sm:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex items-start gap-3 rounded-xl border border-border bg-bg-base/70 p-4 font-mono text-[13.5px] leading-relaxed text-fg sm:text-sm">
                  <span className="select-none text-accent">$</span>
                  <code className="flex-1 overflow-x-auto whitespace-pre-wrap break-words">
                    {current.command}
                  </code>
                  <button
                    onClick={copy}
                    aria-label="Copy command"
                    className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-border bg-bg-raised text-fg-muted transition hover:border-accent/50 hover:text-accent"
                  >
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                  </button>
                </div>

                <p className="mt-4 text-sm leading-relaxed text-fg-muted">
                  {current.hint}
                </p>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      <p className="mx-auto mt-10 max-w-xl text-center text-xs text-fg-dim">
        After install: <span className="font-mono text-fg-muted">quell init</span>{" "}
        &middot; <span className="font-mono text-fg-muted">quell doctor</span> &middot;{" "}
        <span className="font-mono text-fg-muted">quell watch</span>.
      </p>
    </section>
  );
}
