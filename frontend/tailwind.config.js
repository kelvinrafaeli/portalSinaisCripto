/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // TradingView-inspired dark theme
        background: {
          DEFAULT: '#131722',
          secondary: '#1e222d',
          tertiary: '#2a2e39',
        },
        foreground: {
          DEFAULT: '#d1d4dc',
          muted: '#787b86',
        },
        border: {
          DEFAULT: '#363a45',
          light: '#434651',
        },
        // Signal colors
        long: {
          DEFAULT: '#26a69a',
          light: '#4db6ac',
          dark: '#00796b',
        },
        short: {
          DEFAULT: '#ef5350',
          light: '#e57373',
          dark: '#c62828',
        },
        // Accent colors
        accent: {
          blue: '#2196f3',
          purple: '#9c27b0',
          orange: '#ff9800',
          yellow: '#ffeb3b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'signal-flash': 'signal-flash 0.5s ease-out',
      },
      keyframes: {
        'signal-flash': {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
