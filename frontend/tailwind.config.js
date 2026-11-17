/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // DevCrew dark theme palette
        bg: {
          base:   '#0d1117',
          card:   '#161b22',
          raised: '#1c2128',
          border: '#30363d',
        },
        accent: {
          blue:   '#58a6ff',
          green:  '#3fb950',
          yellow: '#d29922',
          red:    '#f85149',
          purple: '#a371f7',
          cyan:   '#39d353',
        },
        text: {
          primary:   '#e6edf3',
          secondary: '#8b949e',
          muted:     '#6e7681',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        glow:       '0 0 20px rgba(88,166,255,0.15)',
        'glow-green':'0 0 20px rgba(63,185,80,0.15)',
        'glow-red': '0 0 20px rgba(248,81,73,0.15)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':    'fadeIn 0.3s ease-out',
        'slide-up':   'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
