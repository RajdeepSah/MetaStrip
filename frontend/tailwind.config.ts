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
        "cyan-primary": "#00d9ff",
        "cyan-dim": "#00a8c4",
        "cyan-ghost": "#003d4d",
        "bg-dark": "#0a0f14",
        "surface": "#111820",
        "surface-raised": "#162130",
        "border-dim": "#1e2d3a",
        "border-bright": "#2a4a5a",
        "text-primary": "#e2eaf0",
        "text-muted": "#4a7a8a",
        "text-dim": "#2a4a5a",
        "risk-red": "#ff4444",
        "risk-amber": "#ffaa00",
        "risk-green": "#00cc88",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(0,217,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,217,255,0.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid": "40px 40px",
      },
    },
  },
  plugins: [],
};

export default config;
