"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export { gsap, ScrollTrigger };

export function useGsap(
  setup: (self: gsap.Context) => void,
  scope?: React.RefObject<HTMLElement | null>,
  deps: ReadonlyArray<unknown> = []
) {
  const setupRef = useRef(setup);
  setupRef.current = setup;

  useEffect(() => {
    const ctx = gsap.context((self) => setupRef.current(self), scope?.current ?? undefined);
    return () => ctx.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

export function prefersMotion() {
  if (typeof window === "undefined") return true;
  return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function isDesktop() {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(min-width: 768px)").matches;
}
