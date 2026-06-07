/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#2563EB",
        secondary: "#F59E0B",
        success: "#10B981",
        error: "#EF4444",
        background: "#F8FAFC",
        surface: "#FFFFFF",
      },
    },
  },
  plugins: [],
}
