<template>
  <div class="mx-auto flex min-h-full max-w-md flex-col px-5 py-8">
    <!-- Hero -->
    <div class="mb-8 mt-4 text-center">
      <div class="mx-auto mb-4 grid h-16 w-16 animate-floaty grid-cols-2 gap-1">
        <div class="rounded-md bg-indigo-500"></div>
        <div class="rounded-md bg-pink-500"></div>
        <div class="rounded-md bg-pink-500"></div>
        <div class="rounded-md bg-indigo-500"></div>
      </div>
      <h1 class="text-3xl font-extrabold tracking-tight">Last Square Standing</h1>
      <p class="mt-2 text-sm text-slate-400">
        Pick a square. Share it with no one. Collisions explode — be the lone
        survivor.
      </p>
    </div>

    <!-- Action card -->
    <div class="rounded-2xl bg-white/5 p-5 ring-1 ring-white/10 backdrop-blur">
      <!-- STEP 1: choose an action -->
      <div v-if="mode === null">
        <button
          class="w-full rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 px-4 py-3.5 text-base font-semibold text-white shadow-lg shadow-indigo-900/40 transition active:scale-[0.98]"
          @click="setMode('create')"
        >
          Create Room
        </button>

        <div class="my-4 flex items-center gap-3 text-xs text-slate-500">
          <div class="h-px flex-1 bg-white/10"></div>
          OR
          <div class="h-px flex-1 bg-white/10"></div>
        </div>

        <button
          class="w-full rounded-xl bg-white/10 px-4 py-3.5 text-base font-semibold text-white ring-1 ring-white/10 transition active:scale-[0.98]"
          @click="setMode('join')"
        >
          Join Room
        </button>
      </div>

      <!-- STEP 2: details for the chosen action -->
      <div v-else>
        <button
          class="mb-4 text-sm text-slate-400 hover:text-white"
          @click="setMode(null)"
        >
          ← Back
        </button>

        <label class="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
          Your name
        </label>
        <input
          ref="nameInput"
          v-model="username"
          maxlength="20"
          placeholder="e.g. Michelle"
          class="w-full rounded-xl border-0 bg-slate-900/70 px-4 py-3 text-base text-white outline-none ring-1 ring-white/10 placeholder:text-slate-500 focus:ring-2 focus:ring-indigo-400"
          @keyup.enter="submit"
        />

        <!-- Create: room name -->
        <template v-if="mode === 'create'">
          <label class="mb-1.5 mt-4 block text-xs font-medium uppercase tracking-wide text-slate-400">
            Room name
          </label>
          <input
            v-model="roomName"
            maxlength="30"
            placeholder="e.g. Friday Game Night"
            class="w-full rounded-xl border-0 bg-slate-900/70 px-4 py-3 text-base text-white outline-none ring-1 ring-white/10 placeholder:text-slate-500 focus:ring-2 focus:ring-indigo-400"
            @keyup.enter="submit"
          />
          <button
            class="mt-4 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 px-4 py-3 text-base font-semibold text-white shadow-lg shadow-indigo-900/40 transition active:scale-[0.98] disabled:opacity-50"
            :disabled="busy"
            @click="submit"
          >
            Create Room
          </button>
        </template>

        <!-- Join: room code -->
        <template v-else>
          <label class="mb-1.5 mt-4 block text-xs font-medium uppercase tracking-wide text-slate-400">
            Room code
          </label>
          <input
            v-model="code"
            maxlength="4"
            placeholder="CODE"
            class="w-full rounded-xl border-0 bg-slate-900/70 px-4 py-3 text-center text-base font-bold uppercase tracking-[0.3em] text-white outline-none ring-1 ring-white/10 placeholder:tracking-normal placeholder:text-slate-500 focus:ring-2 focus:ring-pink-400"
            @input="code = code.toUpperCase()"
            @keyup.enter="submit"
          />
          <button
            class="mt-4 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 px-4 py-3 text-base font-semibold text-white shadow-lg shadow-indigo-900/40 transition active:scale-[0.98] disabled:opacity-50"
            :disabled="busy"
            @click="submit"
          >
            Join Room
          </button>
        </template>
      </div>

      <p v-if="error" class="mt-3 text-center text-sm text-rose-400">{{ error }}</p>
    </div>

    <!-- Rules -->
    <div class="mt-5 rounded-2xl bg-white/5 p-5 text-sm text-slate-300 ring-1 ring-white/10">
      <p class="mb-2 font-semibold text-white">How it works</p>
      <ul class="space-y-1.5 text-slate-400">
        <li>🟦 Each round has a theme — secretly tap one word.</li>
        <li>💥 Words two+ players share explode.</li>
        <li>🏝️ Lone words survive to the next round.</li>
        <li>📉 The grid shrinks every round (5×5 → 2×2).</li>
        <li>👑 Last player standing wins.</li>
      </ul>
    </div>

    <p class="mt-6 text-center text-xs text-slate-600">3–16 players · built on Frappe</p>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { cleanErr } from '@/composables/useGame'

const router = useRouter()
const mode = ref(null) // null | 'create' | 'join'
const username = ref(localStorage.getItem('lss_name') || '')
const roomName = ref('')
const code = ref('')
const error = ref('')
const busy = ref(false)
const nameInput = ref(null)

function setMode(m) {
  mode.value = m
  error.value = ''
  if (m) nextTick(() => nameInput.value?.focus())
}

function saveName() {
  localStorage.setItem('lss_name', username.value.trim())
}

function submit() {
  return mode.value === 'create' ? create() : join()
}

async function create() {
  if (busy.value) return
  if (!username.value.trim()) return (error.value = 'Enter your name first.')
  if (!roomName.value.trim()) return (error.value = 'Give your room a name.')
  busy.value = true
  error.value = ''
  try {
    saveName()
    const res = await api.createRoom(username.value.trim(), roomName.value.trim())
    localStorage.setItem(`lss_token_${res.room_code}`, res.player_token)
    router.push(`/${res.room_code}`)
  } catch (e) {
    error.value = cleanErr(e)
  } finally {
    busy.value = false
  }
}

async function join() {
  if (busy.value) return
  if (!username.value.trim()) return (error.value = 'Enter your name first.')
  if (code.value.trim().length < 4) return (error.value = 'Enter a 4-letter code.')
  busy.value = true
  error.value = ''
  try {
    saveName()
    const res = await api.joinRoom(code.value.trim(), username.value.trim())
    localStorage.setItem(`lss_token_${res.room_code}`, res.player_token)
    router.push(`/${res.room_code}`)
  } catch (e) {
    error.value = cleanErr(e)
  } finally {
    busy.value = false
  }
}
</script>
