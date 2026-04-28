/**
 * Layered background for the hero:
 *   1. a subtle grid (SVG, fixed)
 *   2. a gradient mesh (CSS, fixed)
 *   3. three drifting ember "particles" (pure CSS keyframes — composited)
 *
 * The drift used to be driven by Framer Motion (JS rAF per particle, runs
 * even when the hero is scrolled off). Pure CSS keyframes are GPU-only
 * and the browser pauses them once the layer is offscreen.
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

      {/* Drifting embers — CSS keyframes, GPU compositing only. */}
      <span
        aria-hidden="true"
        className="ember absolute left-[12%] top-[22%] h-56 w-56 rounded-full bg-accent/30 blur-2xl"
        style={{ animationDelay: "0s", animationDuration: "14s" }}
      />
      <span
        aria-hidden="true"
        className="ember absolute right-[16%] top-[18%] h-72 w-72 rounded-full bg-cool/20 blur-2xl"
        style={{ animationDelay: "-1.4s", animationDuration: "16s" }}
      />
      <span
        aria-hidden="true"
        className="ember absolute left-1/2 top-[60%] h-44 w-44 rounded-full bg-accent-glow/25 blur-2xl"
        style={{ animationDelay: "-2.8s", animationDuration: "18s" }}
      />
    </div>
  );
}
