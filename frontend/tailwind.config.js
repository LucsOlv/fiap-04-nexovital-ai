/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Direção visual hospitalar: azul principal (ver spec §8.2).
        brand: {
          DEFAULT: "#1e6fd9",
          foreground: "#ffffff",
        },
        status: {
          normal: "#15803d",
          observacao: "#ca8a04",
          alerta: "#ea580c",
          critico: "#dc2626",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
