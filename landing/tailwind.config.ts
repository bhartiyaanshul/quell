import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark-first palette built for "autonomous on-call at night".
        // Deep indigo-black canvas, warm ember accents for incidents,
        // cool violet secondary for calm intelligence.
        bg: {
          base: "#0a0a0f",
          raised: "#12121a",
          subtle: "#1a1a25",
        },
        fg: {
          DEFAULT: "#fafafa",
          muted: "#a1a1aa",
          dim: "#71717a",
        },
        accent: {
          DEFAULT: "#fb923c", // ember / warm orange
          hi: "#fcd34d",
          glow: "#f59e0b",
        },
        cool: {
          DEFAULT: "#a78bfa", // soft violet
          hi: "#c4b5fd",
          deep: "#7c3aed",
        },
        border: {
          DEFAULT: "#27272a",
          bright: "#3f3f46",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      backgroundImage: {
        "grid-fade":
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(251,146,60,0.10), transparent 80%)",
        "hero-mesh":
          "radial-gradient(at 72% 15%, rgba(251,146,60,0.18) 0, transparent 50%), radial-gradient(at 20% 100%, rgba(167,139,250,0.18) 0, transparent 55%)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 12s linear infinite",
        shimmer: "shimmer 2.2s linear infinite",
        "ember-glow": "ember 3.5s ease-in-out infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        ember: {
          "0%, 100%": {
            opacity: "0.55",
            filter: "drop-shadow(0 0 12px rgba(251,146,60,0.45))",
          },
          "50%": {
            opacity: "1",
            filter: "drop-shadow(0 0 24px rgba(251,146,60,0.75))",
          },
        },
      },
    },
  },
  plugins: [],
};

export default config;
