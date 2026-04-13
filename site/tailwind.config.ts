import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        va: {
          bg: "#fafbfc",
          "bg-alt": "#f1f5f9",
          surface: "#ffffff",
          text: "#0f172a",
          muted: "#64748b",
          faint: "#94a3b8",
          accent: "#8b5cf6",
          "accent-dark": "#7c3aed",
          border: "#e2e8f0",
          terminal: "#0f172a",
        },
        sev: {
          critical: "#dc2626",
          high: "#ea580c",
          medium: "#ca8a04",
          low: "#2563eb",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
