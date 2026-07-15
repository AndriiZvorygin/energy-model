/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#17211e',
        paper: '#f6f7f3',
        petroleum: '#0f766e',
        signal: '#d97706',
        inventory: '#2563eb',
        equity: '#be123c',
      },
      boxShadow: {
        quiet: '0 12px 30px rgba(23, 33, 30, 0.07)',
      },
    },
  },
  plugins: [],
}
