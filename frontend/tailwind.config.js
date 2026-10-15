export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#172D4B',
        blue: '#173C66',
        cloud: '#F7F9FC',
        powder: '#EAF1FA',
        champagne: '#D6B777',
        mint: '#EAF5F0',
        border: '#E2E8F0',
        slate: {
          50: '#F7F9FC',
          100: '#EEF2F7',
          200: '#E2E8F0',
          400: '#8796AA',
          500: '#64748B',
          600: '#465C77',
          700: '#172D4B',
        },
        emerald: { 50: '#EAF5F0', 600: '#42765C', 700: '#315F4B', 800: '#274C3C' },
        amber: { 50: '#F8F3E7', 700: '#80672F', 800: '#6D592C' },
        orange: { 50: '#F8F3E7' },
        rose: { 50: '#FFF1F2', 700: '#9F3343' },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        heading: ['Manrope', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        card: '0 8px 24px rgba(23, 60, 102, .055)',
      },
      borderRadius: {
        card: '18px',
      },
    },
  },
  plugins: [],
};
