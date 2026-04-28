"use client";

import { useEffect, useRef } from "react";

const DEFAULT_GLYPHS = "!<>-_\\/[]{}—=+*^?#________";

type Trigger = "mount" | "inView";

type Props = {
  text: string;
  duration?: number;
  glyphs?: string;
  trigger?: Trigger;
  className?: string;
  as?: keyof JSX.IntrinsicElements;
  delay?: number;
};

/**
 * Character-by-character scramble reveal. Glyphs cycle randomly
 * before each character resolves to its final value.
 *
 * Performance notes:
 *  - Writes to the DOM via ref.textContent (no React state per frame)
 *  - Caps frame rate to ~30fps — visually identical, half the work
 *  - Skipped entirely on small screens (we have ~19 instances on the page)
 *  - Skipped under prefers-reduced-motion
 *  - IntersectionObserver runs the animation once per node
 */
export function TextScramble({
  text,
  duration = 1500,
  glyphs = DEFAULT_GLYPHS,
  trigger = "mount",
  className,
  as: Tag = "span",
  delay = 0,
}: Props) {
  const ref = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof window === "undefined") return;

    // Reset to final text up-front, then optionally scramble.
    node.textContent = text;

    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    if (reduce) return;

    // Skip the (expensive) scramble on small screens — text is small,
    // the effect adds little, and the rAF storm hurts on mobile.
    const isSmall = !window.matchMedia("(min-width: 640px)").matches;
    if (isSmall) return;

    let raf = 0;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    let observer: IntersectionObserver | undefined;
    let started = false;

    const run = () => {
      const start = performance.now() + delay;
      const chars = text.split("");
      let lastFrame = 0;
      // ~30fps cap
      const minFrameMs = 33;

      const tick = (now: number) => {
        if (now - lastFrame < minFrameMs) {
          raf = requestAnimationFrame(tick);
          return;
        }
        lastFrame = now;

        const elapsed = Math.max(0, now - start);
        const progress = Math.min(1, elapsed / duration);
        const revealed = Math.floor(progress * chars.length);

        let next = "";
        for (let i = 0; i < chars.length; i++) {
          const ch = chars[i];
          if (ch === " ") next += " ";
          else if (i < revealed) next += ch;
          else next += glyphs[(Math.random() * glyphs.length) | 0];
        }
        node.textContent = next;

        if (progress < 1) {
          raf = requestAnimationFrame(tick);
        } else {
          node.textContent = text;
        }
      };

      raf = requestAnimationFrame(tick);
    };

    if (trigger === "mount") {
      timeout = setTimeout(run, 0);
    } else {
      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting && !started) {
              started = true;
              run();
              observer?.disconnect();
            }
          }
        },
        { threshold: 0.4 }
      );
      observer.observe(node);
    }

    return () => {
      if (raf) cancelAnimationFrame(raf);
      if (timeout) clearTimeout(timeout);
      observer?.disconnect();
    };
  }, [text, duration, glyphs, trigger, delay]);

  const Component = Tag as React.ElementType;
  return (
    <Component
      ref={ref}
      className={`scramble ${className ?? ""}`}
      aria-label={text}
    >
      {text}
    </Component>
  );
}
