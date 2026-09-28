/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          DEFAULT: "#6ecfa3",
          dark: "#53ba8d",
          light: "#e8faf3",
          muted: "#d1f5e5",
          ink: "#1a4a2e",
        },
        ink: "#111827",
        // rb.* kept so existing bg-rb-navy / bg-rb-teal classes across the
        // app inherit the new palette without touching every call site.
        rb: {
          navy: "#111827",
          teal: "#53ba8d",
          amber: "#b45309",
        },
      },
      borderRadius: {
        xl: "14px",
        "2xl": "18px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.04)",
        "card-hover": "0 8px 24px rgba(0,0,0,0.06)",
      },
      keyframes: {
        fadeUp: { from: { opacity: 0, transform: "translateY(12px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        countUp: { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        pulseBrand: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(110,207,163,0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(110,207,163,0)" },
        },
      },
      animation: {
        fadeUp: "fadeUp 0.4s ease both",
        countUp: "countUp 0.5s ease both",
        pulseBrand: "pulseBrand 2.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
