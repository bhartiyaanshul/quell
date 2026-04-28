"use client";

import { motion } from "framer-motion";

import { SectionHeader } from "@/components/SectionHeader";
import { TerminalDemo } from "@/components/TerminalDemo";

export function TerminalShowcase() {
  return (
    <section
      id="watch"
      className="relative bg-bg-base py-28 md:py-36"
    >
      <div className="mx-auto max-w-6xl px-6">
        <SectionHeader
          eyebrow="Watch it work"
          title={
            <>
              A real <span className="font-mono text-accent">quell watch</span>{" "}
              session, in&nbsp;your terminal.
            </>
          }
          body="Tail your logs locally, detect a new error signature, spawn the IncidentCommander, run sandboxed tools, finish in seconds. No cloud, no telemetry."
        />

        <motion.div
          initial={{ opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="relative mx-auto mt-14 max-w-4xl"
        >
          {/* halo */}
          <div
            aria-hidden
            className="absolute -inset-x-12 -inset-y-8 -z-10 rounded-[2.5rem] bg-gradient-to-br from-accent/15 via-transparent to-cool/15 blur-3xl"
          />
          <TerminalDemo />
        </motion.div>
      </div>
    </section>
  );
}
