import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "rgb(var(--border-muted) / <alpha-value>)",
        input: "rgb(var(--border-muted) / <alpha-value>)",
        ring: "rgb(var(--accent-primary) / <alpha-value>)",
        background: "rgb(var(--bg-primary) / <alpha-value>)",
        foreground: "rgb(var(--text-primary) / <alpha-value>)",
        glass: "rgb(var(--bg-glass) / <alpha-value>)",
        primary: {
          DEFAULT: "rgb(var(--accent-primary) / <alpha-value>)",
          foreground: "rgb(var(--text-on-accent) / <alpha-value>)",
        },
        secondary: {
          DEFAULT: "rgb(var(--bg-secondary) / <alpha-value>)",
          foreground: "rgb(var(--text-primary) / <alpha-value>)",
        },
        destructive: {
          DEFAULT: "rgb(var(--danger) / <alpha-value>)",
          foreground: "rgb(var(--text-on-danger) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "rgb(var(--bg-secondary) / <alpha-value>)",
          foreground: "rgb(var(--text-muted) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--accent-muted) / <alpha-value>)",
          foreground: "rgb(var(--text-on-accent) / <alpha-value>)",
        },
        popover: {
          DEFAULT: "rgb(var(--bg-secondary) / <alpha-value>)",
          foreground: "rgb(var(--text-primary) / <alpha-value>)",
        },
        card: {
          DEFAULT: "rgb(var(--bg-secondary) / <alpha-value>)",
          foreground: "rgb(var(--text-primary) / <alpha-value>)",
        },
        sidebar: {
          DEFAULT: "rgb(var(--bg-secondary) / <alpha-value>)",
          foreground: "rgb(var(--text-primary) / <alpha-value>)",
          primary: "rgb(var(--accent-primary) / <alpha-value>)",
          "primary-foreground": "rgb(var(--text-on-accent) / <alpha-value>)",
          accent: "rgb(var(--bg-glass) / <alpha-value>)",
          "accent-foreground": "rgb(var(--text-primary) / <alpha-value>)",
          border: "rgb(var(--border-muted) / <alpha-value>)",
          ring: "rgb(var(--accent-primary) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      borderRadius: {
        lg: "var(--radius-lg)",
        md: "var(--radius-md)",
        sm: "var(--radius-sm)",
      },
      boxShadow: {
        'soft': 'var(--shadow-soft)',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;