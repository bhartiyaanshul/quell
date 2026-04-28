"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

import { SectionHeader } from "@/components/SectionHeader";
import { TextScramble } from "@/components/TextScramble";
import { SKILLS_SHOWCASE } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function SkillsShowcase() {
  return (
    <section
      id="skills"
      className="relative bg-bg-base py-32 md:py-44"
    >
      {/* soft top hairline so stacked sections meet cleanly */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-border-bright/40 to-transparent"
      />

      <div className="mx-auto max-w-6xl px-6">
        <SectionHeader
          eyebrow="Skills"
          title={
            <>
              19 runbooks. Auto-injected when{" "}
              <span className="text-gradient">triggers match.</span>
            </>
          }
          body="Each skill is a markdown + YAML runbook. The detector matches an incident's signature against trigger globs; matched skills are appended to the agent's system prompt for that investigation."
        />

        <div className="mt-16 grid grid-cols-1 gap-7 md:grid-cols-2">
          {SKILLS_SHOWCASE.map((skill, i) => (
            <SkillCard key={skill.id} skill={skill} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function SkillCard({
  skill,
  index,
}: {
  skill: (typeof SKILLS_SHOWCASE)[number];
  index: number;
}) {
  const [active, setActive] = useState(0);
  const [hovered, setHovered] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!hovered) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
      setActive(0);
      return;
    }
    intervalRef.current = setInterval(() => {
      setActive((prev) => (prev + 1) % skill.slides.length);
    }, 1500);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [hovered, skill.slides.length]);

  return (
    <motion.article
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group relative overflow-hidden rounded-2xl border border-border bg-bg-raised/60 backdrop-blur transition-colors duration-500 hover:border-border-bright"
    >
      <div className="relative aspect-[3/2] w-full overflow-hidden bg-bg-subtle">
        {skill.slides.map((src, i) => (
          <Image
            key={src}
            src={src}
            alt={`${skill.title} — frame ${i + 1}`}
            fill
            sizes="(max-width: 768px) 100vw, 50vw"
            priority={index < 2 && i === 0}
            className={cn(
              "object-cover transition-opacity duration-700",
              i === active ? "opacity-100" : "opacity-0"
            )}
          />
        ))}

        {/* slide indicator */}
        <div className="absolute bottom-3 left-3 flex gap-1.5">
          {skill.slides.map((_, i) => (
            <span
              key={i}
              className={cn(
                "h-1 w-6 rounded-full transition-colors duration-300",
                i === active ? "bg-accent" : "bg-fg/20"
              )}
            />
          ))}
        </div>

        {/* hover arrow */}
        <span
          aria-hidden
          className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-bg-base/70 text-fg opacity-0 backdrop-blur transition-all duration-500 group-hover:opacity-100"
        >
          <ArrowUpRight size={16} />
        </span>
      </div>

      <div className="p-5">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-base font-semibold text-fg">
            <TextScramble text={skill.title} trigger="inView" duration={1100} />
          </h3>
          <span className="text-xs text-fg-dim">{skill.year}</span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-fg-muted">
          {skill.description}
        </p>
        <div className="mt-4 flex flex-wrap gap-1.5">
          {skill.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-border bg-bg-base/60 px-2.5 py-0.5 text-[11px] font-medium text-fg-dim"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </motion.article>
  );
}
