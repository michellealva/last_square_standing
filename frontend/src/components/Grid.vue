<template>
  <div
    class="mx-auto grid w-full max-w-[min(90vw,28rem)] gap-2 sm:gap-3"
    :style="{ gridTemplateColumns: `repeat(${size}, minmax(0, 1fr))` }"
  >
    <button
      v-for="cell in cells"
      :key="cell.index"
      type="button"
      :disabled="mode !== 'select' || disabled || cell.frozen"
      class="relative aspect-square select-none rounded-xl ring-1 transition-all duration-150 motion-reduce:animate-none"
      :class="cellClass(cell)"
      :style="cell.exploded || cell.bombed ? { animationDelay: `${(cell.index % 5) * 60}ms` } : null"
      @click="onPick(cell)"
    >
      <!-- corner markers -->
      <span v-if="cell.frozen" class="absolute left-1 top-1 text-sm">❄️</span>
      <span v-else-if="cell.bonus && mode === 'select'" class="absolute left-1 top-1 text-sm">⭐</span>

      <!-- select mode: word label + my-pick check -->
      <template v-if="mode === 'select'">
        <span
          class="absolute inset-0 grid place-items-center px-1 text-center text-xs font-semibold leading-tight sm:text-sm"
          :class="cell.frozen ? 'text-slate-500' : cell.index === mySquare ? 'text-white' : 'text-slate-200'"
        >
          {{ cell.label }}
        </span>
        <span v-if="cell.index === mySquare" class="absolute right-1 top-1 text-sm">✓</span>
      </template>

      <!-- reveal mode: word label + occupants -->
      <template v-else>
        <span
          v-if="cell.bombed"
          class="absolute -right-1 -top-3 animate-pop text-2xl drop-shadow motion-reduce:animate-none"
          :style="{ animationDelay: `${(cell.index % 5) * 60}ms` }"
          >💣</span
        >
        <span
          v-else-if="cell.exploded"
          class="absolute -right-1 -top-3 animate-pop text-2xl drop-shadow motion-reduce:animate-none"
          :style="{ animationDelay: `${(cell.index % 5) * 60}ms` }"
          >💥</span
        >
        <span v-else-if="cell.tiebreakLoser" class="absolute -top-2 right-0 text-lg drop-shadow">⏱️</span>
        <span v-else-if="cell.bonus" class="absolute -top-2 right-0 text-lg drop-shadow">⭐</span>
        <span
          v-if="cell.label"
          class="absolute inset-x-0 top-1 truncate px-1 text-center text-[10px] font-medium text-slate-400 sm:text-xs"
        >
          {{ cell.label }}
        </span>
        <div class="absolute inset-0 flex flex-wrap content-center items-center justify-center gap-0.5 p-1">
          <span
            v-for="(name, i) in cell.occupants"
            :key="i"
            class="grid h-6 w-6 place-items-center rounded-full text-[10px] font-bold ring-2 ring-black/20"
            :class="cell.exploded || cell.bombed ? 'bg-rose-200 text-rose-900' : cell.tiebreakLoser ? 'bg-sky-200 text-sky-900' : 'bg-emerald-200 text-emerald-900'"
            :title="name"
          >
            {{ initials(name) }}
          </span>
        </div>
      </template>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: Number, required: true },
  mode: { type: String, default: 'select' }, // 'select' | 'reveal'
  mySquare: { type: Number, default: -1 },
  selections: { type: Array, default: () => [] }, // [{username, square}]
  explodedSquares: { type: Array, default: () => [] },
  bombedSquares: { type: Array, default: () => [] },
  tiebreakSquare: { type: Number, default: -1 }, // square of the slowest-picker out
  frozen: { type: Array, default: () => [] }, // locked, unpickable tiles
  bonusSquare: { type: Number, default: -1 },
  labels: { type: Array, default: () => [] }, // word shown on each tile, by index
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['pick'])

const explodedSet = computed(() => new Set(props.explodedSquares))
const bombedSet = computed(() => new Set(props.bombedSquares))
const frozenSet = computed(() => new Set(props.frozen))

const occupantsBySquare = computed(() => {
  const map = {}
  for (const s of props.selections) {
    ;(map[s.square] ||= []).push(s.username)
  }
  return map
})

const cells = computed(() => {
  const total = props.size * props.size
  return Array.from({ length: total }, (_, index) => ({
    index,
    occupants: occupantsBySquare.value[index] || [],
    exploded: explodedSet.value.has(index),
    bombed: bombedSet.value.has(index),
    frozen: frozenSet.value.has(index),
    bonus: index === props.bonusSquare,
    tiebreakLoser: index === props.tiebreakSquare,
    label: props.labels[index] || '',
  }))
})

function cellClass(cell) {
  if (props.mode === 'select') {
    if (cell.frozen) return 'bg-slate-800/60 ring-white/5 cursor-not-allowed opacity-60'
    if (cell.index === props.mySquare) {
      return 'bg-indigo-500 ring-indigo-300 text-white scale-[1.02] shadow-lg shadow-indigo-900/50'
    }
    if (cell.bonus) return 'bg-amber-400/15 ring-amber-300/50 hover:bg-amber-400/25 active:scale-95'
    return 'bg-white/5 ring-white/10 hover:bg-white/10 active:scale-95'
  }
  // reveal
  if (cell.exploded || cell.bombed) return 'bg-rose-500/25 ring-rose-400/60 animate-explode'
  if (cell.tiebreakLoser) return 'bg-sky-500/20 ring-sky-400/50'
  if (cell.occupants.length === 1) return 'bg-emerald-500/20 ring-emerald-400/50'
  return 'bg-white/[0.03] ring-white/5'
}

function onPick(cell) {
  if (props.mode === 'select' && !props.disabled && !cell.frozen) emit('pick', cell.index)
}

function initials(name) {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}
</script>
