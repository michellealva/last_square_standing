import frappeUIPreset from 'frappe-ui/tailwind'
import colors from 'tailwindcss/colors'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // frappe-ui's preset overrides theme.colors with its own palette, dropping
      // Tailwind's defaults. Restore the families this game's UI is built on.
      colors: {
        slate: colors.slate,
        indigo: colors.indigo,
        pink: colors.pink,
        rose: colors.rose,
        emerald: colors.emerald,
        amber: colors.amber,
        sky: colors.sky,
        orange: colors.orange,
      },
      keyframes: {
        explode: {
          '0%': { transform: 'scale(1)', filter: 'brightness(1)' },
          '30%': { transform: 'scale(1.18) rotate(-2deg)', filter: 'brightness(1.6)' },
          '60%': { transform: 'scale(0.92) rotate(2deg)' },
          '100%': { transform: 'scale(1)', filter: 'brightness(1)' },
        },
        pop: {
          '0%': { transform: 'scale(0.6)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        floaty: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        shake: {
          '0%,100%': { transform: 'translateX(0)' },
          '20%': { transform: 'translateX(-4px) rotate(-1deg)' },
          '40%': { transform: 'translateX(4px) rotate(1deg)' },
          '60%': { transform: 'translateX(-3px)' },
          '80%': { transform: 'translateX(3px)' },
        },
        tickpulse: {
          '0%,100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.35)' },
        },
        'confetti-fall': {
          '0%': { transform: 'translateY(-10%) translateX(0) rotate(0deg)', opacity: '1' },
          '100%': {
            transform: 'translateY(105vh) translateX(var(--drift, 0)) rotate(var(--rot, 360deg))',
            opacity: '0',
          },
        },
      },
      animation: {
        explode: 'explode 0.6s ease-in-out',
        pop: 'pop 0.25s ease-out',
        floaty: 'floaty 3s ease-in-out infinite',
        shake: 'shake 0.5s ease-in-out',
        tickpulse: 'tickpulse 1s ease-in-out infinite',
        'confetti-fall': 'confetti-fall linear forwards',
      },
    },
  },
  plugins: [],
}
