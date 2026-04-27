import type { Config } from "tailwindcss";

// Forked from landing/tailwind.config.ts so the dashboard reads as a
// sibling surface to the marketing site — same palette + typography.
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: { base: "#0a0a0f", raised: "#12121a", subtle: "#1a1a25" },
        fg: { DEFAULT: "#fafafa", muted: "#a1a1aa", dim: "#71717a" },
        accent: { DEFAULT: "#fb923c", hi: "#fcd34d", glow: "#f59e0b" },
        cool: { DEFAULT: "#a78bfa", hi: "#c4b5fd", deep: "#7c3aed" },
        border: { DEFAULT: "#27272a", bright: "#3f3f46" },
        ok: { DEFAULT: "#22c55e" },
        warn: { DEFAULT: "#fcd34d" },
        crit: { DEFAULT: "#dc2626" },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
