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
        brand: {
          dark: "#0B192C",
          navy: "#102A46",
          blue: "#1D5EFF",
          teal: "#12B8A6",
          purple: "#8057E8",
          orange: "#FF821C",
          green: "#10B981",
          bg: "#F7F9FC",
          card: "#FFFFFF",
          border: "#E2E8F0",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
