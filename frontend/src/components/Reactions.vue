<template>
  <div class="pointer-events-none fixed inset-0 z-40 overflow-hidden">
    <div
      v-for="r in reactions"
      :key="r.id"
      class="absolute bottom-24 flex animate-float-up flex-col items-center motion-reduce:animate-none"
      :style="{ left: lane(r.id) }"
    >
      <span class="text-4xl drop-shadow">{{ r.emoji }}</span>
      <span class="mt-0.5 max-w-[6rem] truncate rounded-full bg-black/40 px-2 text-[10px] text-white/80">
        {{ r.username }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  reactions: { type: Array, default: () => [] },
})

// Spread reactions across a few horizontal lanes so they don't fully overlap.
function lane(id) {
  const lanes = [15, 32, 50, 68, 85]
  return `${lanes[id % lanes.length]}%`
}
</script>
