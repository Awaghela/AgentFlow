/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B0F14",
          900: "#0F141A",
        },
        surface: {
          DEFAULT: "#121820",
          raised: "#182029",
          hover: "#1D2530",
        },
        border: {
          DEFAULT: "#232C36",
          soft: "#1B222B",
        },
        text: {
          primary: "#E7ECF2",
          secondary: "#8B98A5",
          faint: "#5C6773",
        },
        signal: {
          amber: "#F0A83A",
          amberSoft: "#3A2E18",
          green: "#3ABE8E",
          greenSoft: "#173229",
          red: "#E15554",
          redSoft: "#331A1A",
          cyan: "#4FB8D6",
          cyanSoft: "#17262E",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.6)",
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "10px",
      },
    },
  },
  plugins: [],
};
