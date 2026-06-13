<template>
  <div class="relative grid h-16 w-16 place-items-center">
    <svg class="h-16 w-16 -rotate-90" viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="3" />
      <circle
        cx="18"
        cy="18"
        r="15.5"
        fill="none"
        :stroke="strokeColor"
        stroke-width="3"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        class="transition-[stroke-dashoffset] duration-200 ease-linear"
      />
    </svg>
    <span
      class="absolute text-xl font-black tabular-nums motion-reduce:animate-none"
      :class="seconds <= 3 ? 'animate-tickpulse text-rose-400' : 'text-white'"
    >
      {{ seconds }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  seconds: { type: Number, default: 0 },
  total: { type: Number, default: 10 },
  accent: { type: String, default: 'indigo' },
})

const circumference = 2 * Math.PI * 15.5

const offset = computed(() => {
  const frac = Math.max(0, Math.min(1, props.seconds / (props.total || 1)))
  return circumference * (1 - frac)
})

const strokeColor = computed(() => {
  if (props.seconds <= 3) return '#fb7185'
  return props.accent === 'pink' ? '#ec4899' : '#818cf8'
})
</script>
