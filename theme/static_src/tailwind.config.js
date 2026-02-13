/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Templates Django
    '../../templates/**/*.html',
    '../../presentes/templates/**/*.html',
    '../../theme/templates/**/*.html',
    // Python files (for dynamic classes)
    '../../**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        // Tema principal: roxo/gradiente (cor atual da app)
        primary: {
          50:  '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7c3aed',
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },
        // Tema secundário: verde natal
        christmas: {
          green: '#2D5016',
          red:   '#C41E3A',
          gold:  '#FFD700',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in':   'fadeIn 0.3s ease-in-out',
        'slide-up':  'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',    opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        // Tema padrão: Roxo (tema atual da app)
        lista_presentes: {
          'primary':          '#9333ea',
          'primary-content':  '#ffffff',
          'secondary':        '#7c3aed',
          'secondary-content':'#ffffff',
          'accent':           '#FFD700',
          'accent-content':   '#1f2937',
          'neutral':          '#1f2937',
          'neutral-content':  '#ffffff',
          'base-100':         '#0f0820',
          'base-200':         '#1a0e2e',
          'base-300':         '#2d1b4e',
          'base-content':     '#e2d9f3',
          'info':             '#38bdf8',
          'success':          '#4ade80',
          'warning':          '#fbbf24',
          'error':            '#f87171',
        },
      },
      {
        // Tema claro: Roxo/Branco
        lista_presentes_light: {
          'primary':          '#9333ea',
          'primary-content':  '#ffffff',
          'secondary':        '#7c3aed',
          'secondary-content':'#ffffff',
          'accent':           '#FFD700',
          'accent-content':   '#1f2937',
          'neutral':          '#374151',
          'neutral-content':  '#ffffff',
          'base-100':         '#ffffff',
          'base-200':         '#f3f4f6',
          'base-300':         '#e5e7eb',
          'base-content':     '#111827',
          'info':             '#0ea5e9',
          'success':          '#22c55e',
          'warning':          '#f59e0b',
          'error':            '#ef4444',
        },
      },
      'dark',
    ],
    darkTheme: 'lista_presentes',
    base: true,
    styled: true,
    utils: true,
    logs: false,
  },
}
