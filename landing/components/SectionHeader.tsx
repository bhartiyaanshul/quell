"use client";

import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

/**
 * Consistent section header used across the page.
 *
 * Appears from blur + y-offset as the section scrolls into view.
 */
export function SectionHeader({
  eyebrow,
  title,
  body,
  align = "center",
  className,
}: {
  eyebrow?: string;
  title: React.ReactNode;
  body?: React.ReactNode;
  align?: "center" | "left";
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24, filter: "blur(6px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0)" }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl",
        className,
      )}
    >
      {eyebrow && (
        <div
          className={cn(
            "mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/60 px-3 py-1 text-xs font-medium uppercase tracking-[0.12em] text-fg-muted",
          )}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_6px_rgba(251,146,60,0.8)]" />
          {eyebrow}
        </div>
      )}
      <h2 className="text-balance text-4xl font-semibold leading-[1.08] tracking-tight text-fg sm:text-5xl">
        {title}
      </h2>
      {body && (
        <p className="mt-5 text-pretty text-base leading-relaxed text-fg-muted sm:text-lg">
          {body}
        </p>
      )}
    </motion.div>
  );
}
