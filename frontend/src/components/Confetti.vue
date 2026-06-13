<template>
  <div class="pointer-events-none absolute inset-0 overflow-hidden">
    <span
      v-for="p in pieces"
      :key="p.id"
      class="absolute top-0 block h-2 w-2 animate-confetti-fall rounded-[1px]"
      :style="p.style"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const COLORS = ['#818cf8', '#ec4899', '#34d399', '#fbbf24', '#f87171', '#38bdf8']
const pieces = ref([])

onMounted(() => {
  // Respect users who prefer less motion — skip the burst entirely.
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  pieces.value = Array.from({ length: 90 }, (_, id) => {
    const left = Math.random() * 100
    const delay = Math.random() * 0.6
    const duration = 1.8 + Math.random() * 1.6
    const rot = Math.random() * 360
    const drift = (Math.random() * 2 - 1) * 60
    return {
      id,
      style: {
        left: `${left}%`,
        backgroundColor: COLORS[id % COLORS.length],
        animationDelay: `${delay}s`,
        animationDuration: `${duration}s`,
        '--rot': `${rot}deg`,
        '--drift': `${drift}px`,
      },
    }
  })
})
</script>
