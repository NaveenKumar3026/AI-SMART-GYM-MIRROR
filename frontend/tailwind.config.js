/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#060608',
          card: 'rgba(18, 18, 26, 0.65)',
          border: 'rgba(255, 255, 255, 0.07)',
          accent: 'rgba(255, 255, 255, 0.03)',
        },
        brand: {
          cyan: '#00f2fe',
          blue: '#4facfe',
          purple: '#8a2be2',
          magenta: '#ff007f',
          neonGreen: '#39ff14',
          danger: '#ff4d4d',
          warning: '#ffaa00'
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 242, 254, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 242, 254, 0.6)' }
        }
      }
    },
  },
  plugins: [],
}
