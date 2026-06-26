import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary:    "#0052FF",
        "primary-hover": "#003ECB",
        secondary:  "#5B616E",
        neutral:    "#8A919E",
        background: "#F9FAFB",
        surface:    "#FFFFFF",
        "text-primary":   "#050F1A",
        "text-secondary": "#5B616E",
        border:     "#D1D5DB",
        success:    "#05B169",
        warning:    "#F0AD4E",
        error:      "#DF2935",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        chip:  "4px",
        btn:   "8px",
        card:  "12px",
        modal: "16px",
      },
      boxShadow: {
        card:    "0 1px 3px rgba(5,15,26,0.06)",
        dropdown:"0 4px 12px rgba(5,15,26,0.08)",
        modal:   "0 12px 24px rgba(5,15,26,0.12)",
      },
      maxWidth: {
        container: "1200px",
      }
    },
  },
  plugins: [],
};

export default config;