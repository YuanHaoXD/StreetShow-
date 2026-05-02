import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neonPurple: "#B026FF",
        acidGreen: "#7CFF6B",
      },
    },
  },
  plugins: [],
};

export default config;
