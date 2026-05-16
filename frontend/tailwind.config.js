/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: {
        income:  '#22c55e',
        expense: '#ef4444',
        accent:  '#6366f1',
      },
    },
  },
  plugins: [],
}
