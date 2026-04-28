"use client";

import { useEffect, useRef, useState } from "react";

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
 * before each character resolves to its final value. Total time
 * is `duration` (default 1500ms).
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
  const [output, setOutput] = useState(text);
  const [hasRun, setHasRun] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    if (reduce) {
      setOutput(text);
      return;
    }

    let raf: number;
    let timeout: ReturnType<typeof setTimeout>;

    const run = () => {
      const start = performance.now() + delay;
      const chars = text.split("");

      const tick = (now: number) => {
        const elapsed = Math.max(0, now - start);
        const progress = Math.min(1, elapsed / duration);
        const revealed = Math.floor(progress * chars.length);

        const next = chars
          .map((ch, i) => {
            if (ch === " ") return " ";
            if (i < revealed) return ch;
            return glyphs[Math.floor(Math.random() * glyphs.length)];
          })
          .join("");

        setOutput(next);

        if (progress < 1) {
          raf = requestAnimationFrame(tick);
        } else {
          setOutput(text);
        }
      };

      raf = requestAnimationFrame(tick);
    };

    if (trigger === "mount") {
      timeout = setTimeout(run, 0);
    } else {
      const node = ref.current;
      if (!node) return;
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && !hasRun) {
              setHasRun(true);
              run();
            }
          });
        },
        { threshold: 0.4 }
      );
      observer.observe(node);
      return () => {
        observer.disconnect();
        if (raf) cancelAnimationFrame(raf);
      };
    }

    return () => {
      if (raf) cancelAnimationFrame(raf);
      if (timeout) clearTimeout(timeout);
    };
  }, [text, duration, glyphs, trigger, delay, hasRun]);

  const Component = Tag as React.ElementType;
  return (
    <Component
      ref={ref}
      className={`scramble ${className ?? ""}`}
      aria-label={text}
    >
      {output}
    </Component>
  );
}
