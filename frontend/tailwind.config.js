/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#F5F7FB',
        canvas: '#090B10',
        panel: '#11151D',
        muted: '#8C96A8',
        line: '#242B38',
        lime: '#C9F27A',
        violet: '#8B7CFF',
        rose: '#F58DA9',
      },
      boxShadow: { glow: '0 0 0 1px rgba(201,242,122,.08), 0 18px 50px rgba(0,0,0,.24)' },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui'] },
    },
  },
  plugins: [],
}
