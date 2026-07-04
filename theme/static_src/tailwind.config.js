/** @type {import('tailwindcss').Config} */

// Design tokens LPII: cantos generosos, animações suaves
const designTokens = {
  '--rounded-box': '1.5rem',
  '--rounded-btn': '0.75rem',
  '--rounded-badge': '1.9rem',
  '--animation-btn': '0.2s',
  '--animation-input': '0.2s',
  '--btn-focus-scale': '0.97',
  '--border-btn': '1px',
  '--tab-radius': '0.75rem',
};

module.exports = {
  content: [
    '../../templates/**/*.html',
    '../../presentes/templates/**/*.html',
    '../../theme/templates/**/*.html',
    '../../**/*.py',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in':   'fadeIn 0.4s ease-out',
        'slide-up':  'slideUp 0.4s ease-out both',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { transform: 'translateY(16px)', opacity: '0' },
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
        // LPII Light - Design principal (rose + emerald, fundo slate claro)
        lpii_light: {
          'primary':          '#e11d48',
          'primary-content':  '#ffffff',
          'secondary':        '#059669',
          'secondary-content':'#ffffff',
          'accent':           '#d97706',
          'accent-content':   '#ffffff',
          'neutral':          '#1e293b',
          'neutral-content':  '#f8fafc',
          'base-100':         '#ffffff',
          'base-200':         '#f8fafc',
          'base-300':         '#f1f5f9',
          'base-content':     '#1e293b',
          'info':             '#0ea5e9',
          'success':          '#059669',
          'warning':          '#d97706',
          'error':            '#dc2626',
          ...designTokens,
        },
      },
      {
        // LPII Dark - Variante escura (rose + emerald em slate escuro)
        lpii_dark: {
          'primary':          '#fb7185',
          'primary-content':  '#1e293b',
          'secondary':        '#34d399',
          'secondary-content':'#1e293b',
          'accent':           '#fbbf24',
          'accent-content':   '#1e293b',
          'neutral':          '#0f172a',
          'neutral-content':  '#e2e8f0',
          'base-100':         '#0f172a',
          'base-200':         '#1e293b',
          'base-300':         '#334155',
          'base-content':     '#f1f5f9',
          'info':             '#38bdf8',
          'success':          '#34d399',
          'warning':          '#fbbf24',
          'error':            '#fb7185',
          ...designTokens,
        },
      },
      {
        // Emerald Light - Verde natural (mantido como alternativa)
        emerald_light: {
          'primary':          '#059669',
          'primary-content':  '#ffffff',
          'secondary':        '#047857',
          'secondary-content':'#ffffff',
          'accent':           '#d97706',
          'accent-content':   '#ffffff',
          'neutral':          '#1f3d2e',
          'neutral-content':  '#ffffff',
          'base-100':         '#fbfefc',
          'base-200':         '#f0fdf4',
          'base-300':         '#dcfce7',
          'base-content':     '#0a2e1c',
          'info':             '#0ea5e9',
          'success':          '#22c55e',
          'warning':          '#f59e0b',
          'error':            '#ef4444',
          ...designTokens,
        },
      },
      {
        // Ocean Light - Azul profundo limpo
        ocean_light: {
          'primary':          '#0284c7',
          'primary-content':  '#ffffff',
          'secondary':        '#0891b2',
          'secondary-content':'#ffffff',
          'accent':           '#ea580c',
          'accent-content':   '#ffffff',
          'neutral':          '#334155',
          'neutral-content':  '#ffffff',
          'base-100':         '#fbfdff',
          'base-200':         '#f1f5f9',
          'base-300':         '#e2e8f0',
          'base-content':     '#0f172a',
          'info':             '#0ea5e9',
          'success':          '#10b981',
          'warning':          '#f59e0b',
          'error':            '#ef4444',
          ...designTokens,
        },
      },
      {
        // Midnight - Escuro indigo
        midnight: {
          'primary':          '#818cf8',
          'primary-content':  '#ffffff',
          'secondary':        '#a78bfa',
          'secondary-content':'#ffffff',
          'accent':           '#f472b6',
          'accent-content':   '#ffffff',
          'neutral':          '#0f172a',
          'neutral-content':  '#e2e8f0',
          'base-100':         '#020617',
          'base-200':         '#0f172a',
          'base-300':         '#1e293b',
          'base-content':     '#c7d2fe',
          'info':             '#38bdf8',
          'success':          '#34d399',
          'warning':          '#fde68a',
          'error':            '#fca5a5',
          ...designTokens,
        },
      },
    ],
    darkTheme: 'lpii_dark',
    base: true,
    styled: true,
    utils: true,
    logs: false,
  },
}
