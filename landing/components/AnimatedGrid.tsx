"use client";

import { motion } from "framer-motion";

/**
 * Layered background for the hero:
 *   1. a subtle grid (SVG, fixed)
 *   2. a gradient mesh (CSS, fixed)
 *   3. three drifting ember "particles" (motion.divs)
 *
 * The parallax of the drifting dots against the static grid is what
 * gives the hero its "alive" feel.
 */
export function AnimatedGrid() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* Grid */}
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.25]"
        aria-hidden="true"
      >
        <defs>
          <pattern
            id="landing-grid"
            width="44"
            height="44"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M44 0L0 0 0 44"
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="1"
            />
          </pattern>
          <radialGradient id="grid-fade" cx="50%" cy="0%" r="70%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
          </radialGradient>
          <mask id="grid-mask">
            <rect width="100%" height="100%" fill="url(#grid-fade)" />
          </mask>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="url(#landing-grid)"
          mask="url(#grid-mask)"
        />
      </svg>

      {/* Mesh gradient */}
      <div className="absolute inset-0 bg-hero-mesh" />
      <div className="absolute inset-x-0 top-0 h-[320px] bg-grid-fade" />

      {/* Drifting embers */}
      <Ember
        className="left-[12%] top-[22%] h-56 w-56 bg-accent/30"
        delay={0}
        distance={20}
      />
      <Ember
        className="right-[16%] top-[18%] h-72 w-72 bg-cool/20"
        delay={1.4}
        distance={25}
      />
      <Ember
        className="left-1/2 top-[60%] h-44 w-44 bg-accent-glow/25"
        delay={2.8}
        distance={15}
      />
    </div>
  );
}

function Ember({
  className,
  delay,
  distance,
}: {
  className: string;
  delay: number;
  distance: number;
}) {
  return (
    <motion.div
      aria-hidden="true"
      initial={{ y: 0, x: 0, opacity: 0 }}
      animate={{
        y: [0, -distance, 0, distance / 2, 0],
        x: [0, distance / 2, -distance / 2, 0],
        opacity: [0.25, 0.7, 0.45, 0.6, 0.25],
      }}
      transition={{
        duration: 14,
        repeat: Infinity,
        ease: "easeInOut",
        delay,
      }}
      className={`absolute rounded-full blur-3xl mix-blend-screen ${className}`}
    />
  );
}
