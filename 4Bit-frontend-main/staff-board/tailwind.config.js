/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hospital: {
          50: '#F0FDF9',
          100: '#CCFBEE',
          200: '#9BF7DE',
          300: '#5EEAD0',
          400: '#26D0BE',
          500: '#0FA497',
          600: '#0A847C',
          700: '#0C6A65',
          800: '#0E5552',
          900: '#104644',
          950: '#052A2A',
        },
        navy: {
          50: '#F0F5FA',
          100: '#DDE8F4',
          200: '#BFD4EB',
          300: '#94B9DE',
          400: '#649ACD',
          500: '#417EBD',
          600: '#3064A1',
          700: '#285184',
          800: '#23446D',
          900: '#1A3352',
          950: '#0E1D31',
        },
        surface: {
          base: '#F8FAFC',
          card: '#FFFFFF',
          subtle: '#F1F5F9',
          border: '#E2E8F0',
          darkBorder: '#CBD5E1',
        }
      },
      fontFamily: {
        sans: [
          '"Plus Jakarta Sans"',
          'Inter',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
      },
      boxShadow: {
        'soft': '0 2px 10px -2px rgba(15, 23, 42, 0.05), 0 1px 3px -1px rgba(15, 23, 42, 0.04)',
        'card': '0 4px 20px -2px rgba(15, 23, 42, 0.06), 0 2px 6px -1px rgba(15, 23, 42, 0.04)',
        'touch': '0 8px 30px -4px rgba(15, 164, 151, 0.18)',
        'focus-ring': '0 0 0 4px rgba(15, 164, 151, 0.35)',
      },
      fontSize: {
        'touch-lg': ['1.25rem', { lineHeight: '1.75rem', letterSpacing: '-0.01em' }],
        'touch-xl': ['1.5rem', { lineHeight: '2rem', letterSpacing: '-0.02em' }],
        'terminal-title': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.03em' }],
      }
    },
  },
  plugins: [],
}
