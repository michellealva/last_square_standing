<template>
  <div class="mx-auto flex min-h-full max-w-md flex-col px-4 py-5" :class="{ 'animate-shake': shaking }">
    <!-- Top bar -->
    <div class="mb-4 flex items-center justify-between">
      <button class="text-sm text-slate-400 hover:text-white" @click="goHome">
        ← Leave
      </button>
      <button
        class="flex items-center gap-2 rounded-full bg-white/5 px-3 py-1.5 text-sm font-semibold tracking-widest text-white ring-1 ring-white/10 active:scale-95"
        @click="copyCode"
        title="Copy room code"
      >
        {{ roomCode }}
        <span class="text-xs text-slate-400">{{ copied ? '✓' : '⧉' }}</span>
      </button>
      <div class="flex w-14 items-center justify-end gap-2">
        <button
          class="text-base leading-none text-slate-400 transition hover:text-white active:scale-90"
          :title="muted ? 'Unmute' : 'Mute'"
          @click="toggleMute"
        >
          {{ muted ? '🔇' : '🔊' }}
        </button>
        <span v-if="state" class="text-sm text-slate-400">
          <span v-if="state.status === 'Playing'">{{ state.alive_count }}</span>
          <span v-else>{{ state.player_count }}/{{ state.max_players }}</span>
        </span>
      </div>
    </div>

    <p v-if="error" class="mb-3 rounded-lg bg-rose-500/15 px-3 py-2 text-center text-sm text-rose-300">
      {{ error }}
    </p>

    <!-- LOADING -->
    <div v-if="phase === 'loading'" class="flex flex-1 items-center justify-center text-slate-500">
      Loading room…
    </div>

    <!-- LOBBY -->
    <div v-else-if="phase === 'lobby'" class="flex flex-1 flex-col">
      <div class="rounded-2xl bg-white/5 p-5 text-center ring-1 ring-white/10">
        <p v-if="state.room_name" class="mb-1 text-lg font-bold text-white">
          {{ state.room_name }}
        </p>
        <p class="text-xs uppercase tracking-wide text-slate-400">Room Code</p>
        <p class="my-1 text-5xl font-black tracking-[0.2em] text-white">{{ roomCode }}</p>
        <p class="text-sm text-slate-400">Share this code so friends can join.</p>
      </div>

      <div class="mt-4 flex-1 rounded-2xl bg-white/5 p-5 ring-1 ring-white/10">
        <div class="mb-3 flex items-center justify-between">
          <p class="font-semibold text-white">Players</p>
          <span class="text-sm text-slate-400">
            {{ state.player_count }} / {{ state.max_players }}
          </span>
        </div>
        <ul class="space-y-2">
          <li
            v-for="p in state.players"
            :key="p.username"
            class="flex animate-pop items-center gap-3 rounded-xl bg-slate-900/50 px-3 py-2.5 ring-1 ring-white/5"
          >
            <span class="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-pink-500 text-xs font-bold">
              {{ initials(p.username) }}
            </span>
            <span class="flex-1 font-medium">{{ p.username }}</span>
            <span v-if="p.is_host" class="text-xs font-semibold text-amber-400">HOST</span>
            <span v-if="isMe(p)" class="text-xs text-indigo-300">you</span>
          </li>
        </ul>
      </div>

      <div class="mt-4">
        <button
          v-if="amHost"
          class="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 px-4 py-3.5 text-base font-semibold text-white shadow-lg shadow-indigo-900/40 transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="state.player_count < state.min_players || busy"
          @click="start"
        >
          {{
            state.player_count < state.min_players
              ? `Need ${state.min_players - state.player_count} more player(s)`
              : 'Start Game'
          }}
        </button>
        <p v-else class="rounded-xl bg-white/5 px-4 py-3.5 text-center text-sm text-slate-400 ring-1 ring-white/10">
          Waiting for host to start…
        </p>
      </div>
    </div>

    <!-- SELECT -->
    <div v-else-if="phase === 'select'" class="flex flex-1 flex-col">
      <div class="mb-3 flex items-center justify-between">
        <div>
          <p class="text-xs uppercase tracking-wide text-slate-400">Round {{ round.round_number }}</p>
          <p class="text-lg font-bold text-white">{{ round.grid_size }} × {{ round.grid_size }} grid</p>
        </div>
        <CountdownRing :seconds="secondsLeft" :total="round.duration" />
      </div>

      <div class="flex flex-1 flex-col justify-center">
        <div
          v-if="amEliminated"
          class="mb-4 animate-pop rounded-xl bg-slate-700/40 px-4 py-3 text-center text-sm font-semibold text-slate-200 ring-1 ring-white/10"
        >
          👀 Spectating — {{ state.alive_count }} player{{ state.alive_count === 1 ? '' : 's' }} still in
        </div>
        <template v-else>
          <p v-if="round.prompt" class="mb-1 text-center text-base font-bold text-white">
            {{ round.prompt }}
          </p>
          <p class="mb-4 text-center text-sm text-slate-300">
            <template v-if="mySquare >= 0">✓ Locked in. Tap another to change.</template>
            <template v-else>Pick one no one else will!</template>
          </p>
        </template>

        <Grid
          :size="round.grid_size"
          mode="select"
          :my-square="mySquare"
          :labels="round.labels"
          :disabled="amEliminated || busy"
          :class="amEliminated ? 'pointer-events-none opacity-40' : ''"
          @pick="pick"
        />

        <p class="mt-5 text-center text-sm text-slate-400">
          {{ round.submitted_count }} of {{ state.alive_count }} players locked in
        </p>
      </div>
    </div>

    <!-- REVEAL -->
    <div v-else-if="phase === 'reveal'" class="flex flex-1 flex-col">
      <div class="mb-3 flex items-center justify-between">
        <div>
          <p class="text-xs uppercase tracking-wide text-slate-400">
            Round {{ reveal?.round_number }} results
          </p>
          <p class="text-lg font-bold text-white">Next round in {{ secondsLeft }}s</p>
        </div>
        <CountdownRing :seconds="secondsLeft" :total="5" accent="pink" />
      </div>

      <div v-if="reveal" class="flex flex-1 flex-col justify-center">
        <p
          v-if="reveal.replay"
          class="mb-4 animate-pop rounded-xl bg-amber-400/15 px-4 py-3 text-center text-sm font-semibold text-amber-200"
        >
          😮 Everyone collided — nobody survived! Replaying this round.
        </p>
        <p
          v-else-if="reveal.tiebreak"
          class="mb-4 animate-pop rounded-xl bg-sky-400/15 px-4 py-3 text-center text-sm font-semibold text-sky-200"
        >
          ⏱️ Nowhere left to shrink — slowest to lock in is out.
        </p>
        <p
          v-else-if="reveal.shrink_only"
          class="mb-4 animate-pop rounded-xl bg-indigo-400/15 px-4 py-3 text-center text-sm font-semibold text-indigo-200"
        >
          🤝 No collisions — everyone's safe, the grid shrinks!
        </p>

        <Grid
          :size="reveal.grid_size"
          mode="reveal"
          :selections="reveal.selections"
          :exploded-squares="reveal.exploded_squares"
          :tiebreak-square="reveal.tiebreak ? reveal.tiebreak_square : -1"
          :labels="reveal.labels || []"
        />

        <div class="mt-5 grid grid-cols-2 gap-3">
          <div class="rounded-xl bg-emerald-500/10 p-3 ring-1 ring-emerald-400/30">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-300">
              Survived
            </p>
            <p v-if="!reveal.survivors.length" class="text-sm text-slate-400">—</p>
            <p v-else class="text-sm text-slate-100">{{ reveal.survivors.join(', ') }}</p>
          </div>
          <div class="rounded-xl bg-rose-500/10 p-3 ring-1 ring-rose-400/30">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-rose-300">
              Eliminated
            </p>
            <p v-if="!reveal.eliminated.length" class="text-sm text-slate-400">—</p>
            <p v-else class="text-sm text-slate-100">{{ reveal.eliminated.join(', ') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- WINNER -->
    <div v-else-if="phase === 'winner'" class="relative flex flex-1 flex-col">
      <Confetti />
      <div class="relative rounded-2xl bg-gradient-to-b from-amber-400/20 to-transparent p-6 text-center ring-1 ring-amber-400/30">
        <div class="mb-2 text-6xl animate-floaty">👑</div>
        <p class="text-sm uppercase tracking-widest text-amber-300">Winner</p>
        <p class="text-3xl font-black text-white">{{ state.winner_name }}</p>
      </div>

      <div class="mt-4 flex-1 rounded-2xl bg-white/5 p-5 ring-1 ring-white/10">
        <p class="mb-3 font-semibold text-white">Final Rankings</p>
        <ol class="space-y-2">
          <li
            v-for="(r, i) in state.rankings"
            :key="r.username"
            class="flex items-center gap-3 rounded-xl px-3 py-2.5"
            :class="rankClass(r.place)"
          >
            <span class="w-6 text-center text-lg">{{ medal(r.place) }}</span>
            <span class="flex-1 font-medium">{{ r.username }}</span>
            <span class="text-sm font-bold text-indigo-200">+{{ r.points }}</span>
          </li>
        </ol>
      </div>

      <div class="mt-4 space-y-2">
        <template v-if="amHost">
          <button
            class="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 px-4 py-3.5 text-base font-semibold text-white shadow-lg transition active:scale-[0.98] disabled:opacity-50"
            :disabled="busy"
            @click="rematch"
          >
            Play Again
          </button>
          <button
            class="w-full rounded-xl bg-white/10 px-4 py-3 text-sm font-semibold text-white ring-1 ring-white/10 transition active:scale-[0.98] disabled:opacity-50"
            :disabled="busy"
            @click="toLobby"
          >
            Back to Lobby (add or change players)
          </button>
        </template>
        <p
          v-else
          class="rounded-xl bg-white/5 px-4 py-3 text-center text-sm text-slate-400 ring-1 ring-white/10"
        >
          Waiting for host to start a new game…
        </p>
        <button
          class="w-full rounded-xl bg-white/10 px-4 py-3 text-base font-semibold text-white ring-1 ring-white/10 active:scale-[0.98]"
          @click="goHome"
        >
          Leave Game
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGame, cleanErr } from '@/composables/useGame'
import { api } from '@/api'
import Grid from '@/components/Grid.vue'
import CountdownRing from '@/components/CountdownRing.vue'
import Confetti from '@/components/Confetti.vue'
import { muted, toggleMute, playPick, playTick, playExplosion, playWin } from '@/sound'

const props = defineProps({ roomCode: { type: String, required: true } })
const router = useRouter()

const game = useGame(props.roomCode)
const { state, error, phase, round, secondsLeft, playerToken } = game
const roomCode = game.roomCode

const busy = ref(false)
const copied = ref(false)
const mySquare = ref(-1)
const shaking = ref(false)

const reveal = computed(() => state.value?.reveal || null)
const me = computed(() => state.value?.me || null)
const amHost = computed(() => !!me.value?.is_host)
const amEliminated = computed(() => !!me.value?.eliminated)

onMounted(() => game.start())

// Reset my pick whenever a fresh round begins.
watch(
  () => round.value && round.value.round_number + '-' + round.value.started_at,
  () => {
    mySquare.value = -1
  },
)

// Keep the highlighted tile in sync with the server's record of MY pick, so it
// survives polls, socket updates, reloads, and reconnects. We only adopt a
// non-null server value, so an in-flight poll can never wipe an optimistic pick.
watch(
  () => me.value?.selected_square,
  (sq) => {
    if (sq !== null && sq !== undefined) mySquare.value = sq
  },
  { immediate: true },
)

// --- Juice: sound + shake driven off phase / countdown transitions ---

// Tense final-countdown ticks (3, 2, 1) while choosing.
watch(secondsLeft, (now, before) => {
  if (phase.value !== 'select' || amEliminated.value) return
  if (now !== before && now >= 1 && now <= 3) playTick()
})

// React to entering the reveal (explosion) and winner (fanfare) phases.
watch(phase, (now, before) => {
  if (now === before) return
  if (now === 'reveal' && reveal.value?.exploded_squares?.length) {
    playExplosion()
    if (!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      shaking.value = true
      setTimeout(() => (shaking.value = false), 500)
    }
  } else if (now === 'winner') {
    playWin()
  }
})

async function pick(index) {
  if (busy.value || amEliminated.value) return
  navigator.vibrate?.(10)
  playPick()
  const prev = mySquare.value
  mySquare.value = index // optimistic
  try {
    await api.submitSelection(roomCode, playerToken.value, index)
  } catch (e) {
    mySquare.value = prev
    error.value = cleanErr(e)
  }
}

async function start() {
  busy.value = true
  try {
    game.applyState(await api.startGame(roomCode, playerToken.value))
  } catch (e) {
    error.value = cleanErr(e)
  } finally {
    busy.value = false
  }
}

async function rematch() {
  busy.value = true
  try {
    game.applyState(await api.restartGame(roomCode, playerToken.value))
  } catch (e) {
    error.value = cleanErr(e)
  } finally {
    busy.value = false
  }
}

async function toLobby() {
  busy.value = true
  try {
    game.applyState(await api.playAgain(roomCode, playerToken.value))
  } catch (e) {
    error.value = cleanErr(e)
  } finally {
    busy.value = false
  }
}

function goHome() {
  game.stop()
  router.push('/')
}

function copyCode() {
  try {
    navigator.clipboard.writeText(roomCode)
  } catch (e) {
    /* ignore */
  }
  copied.value = true
  setTimeout(() => (copied.value = false), 1200)
}

function isMe(p) {
  return me.value && p.username === me.value.username
}
function initials(name) {
  const parts = (name || '').trim().split(/\s+/)
  return parts.length === 1
    ? parts[0].slice(0, 2).toUpperCase()
    : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}
function medal(place) {
  return { 1: '🥇', 2: '🥈', 3: '🥉' }[place] || place
}
function rankClass(place) {
  if (place === 1) return 'bg-amber-400/10'
  if (place === 2) return 'bg-slate-400/10'
  if (place === 3) return 'bg-orange-500/10'
  return 'bg-slate-900/40'
}
</script>
