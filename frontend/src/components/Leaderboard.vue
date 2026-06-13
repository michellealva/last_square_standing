<template>
  <div class="rounded-2xl bg-white/5 p-5 ring-1 ring-white/10">
    <p class="mb-3 flex items-center gap-2 font-semibold text-white">
      🏆 Leaderboard
    </p>
    <div v-if="!rows.length" class="text-sm text-slate-500">
      No games played yet. Be the first champion!
    </div>
    <ol v-else class="space-y-1.5">
      <li
        v-for="(r, i) in rows"
        :key="r.username"
        class="flex items-center gap-3 rounded-lg px-2 py-1.5 text-sm"
        :class="i === 0 ? 'bg-amber-400/10' : ''"
      >
        <span class="w-5 text-center font-bold text-slate-400">{{ i + 1 }}</span>
        <span class="flex-1 truncate font-medium text-slate-100">{{ r.username }}</span>
        <span class="text-xs text-slate-500">{{ r.wins }}W · {{ r.games_played }}G</span>
        <span class="w-12 text-right font-bold text-indigo-300">{{ r.total_score }}</span>
      </li>
    </ol>
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Array, default: () => [] },
})
</script>
