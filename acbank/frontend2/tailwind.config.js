/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // todos los archivos React
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2563EB", // azul personalizado
        secondary: "#FBBF24", // amarillo
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
