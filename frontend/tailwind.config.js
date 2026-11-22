/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: "#0b0d12",
          900: "#11141b",
          850: "#161a24",
          800: "#1c212d",
          700: "#252b3a",
          600: "#323a4d",
        },
        accent: {
          indigo: "#6366f1",
          cyan: "#22d3ee",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "Segoe UI",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset",
      },
    },
  },
  plugins: [],
};