import { ref, computed, onUnmounted } from 'vue'
import { api } from '@/api'
import { initSocket } from '@/socket'

/**
 * Drives a single room's client state.
 *
 * Timing is server-authoritative: the server stamps `server_now`, `started_at`
 * and `deadline` on every state payload. We measure clock skew once per update
 * and run all countdowns against the server clock, so no client can cheat time.
 * Round resolution is triggered by whichever client first crosses the deadline
 * (the server makes it idempotent), with a 2s poll as a safety net.
 */
export function useGame(roomCode) {
  roomCode = (roomCode || '').toUpperCase()
  const state = ref(null)
  const error = ref('')
  const tick = ref(Date.now()) // bumped every frame to drive reactive countdowns

  let skew = 0 // Date.now() - server_now (ms)
  let socket = null
  let pollTimer = null
  let tickTimer = null
  let resolving = false

  const tokenKey = `lss_token_${roomCode}`
  const playerToken = ref(localStorage.getItem(tokenKey) || null)

  // Floating emoji reactions (ephemeral, realtime).
  const reactions = ref([])
  let reactionSeq = 0
  function onReaction(r) {
    if (!r || !r.emoji) return
    const id = ++reactionSeq
    reactions.value.push({ id, username: r.username, emoji: r.emoji })
    setTimeout(() => {
      reactions.value = reactions.value.filter((x) => x.id !== id)
    }, 2600)
  }
  function react(emoji) {
    api.sendReaction(roomCode, playerToken.value, emoji).catch(() => {})
  }

  function setToken(t) {
    playerToken.value = t
    if (t) localStorage.setItem(tokenKey, t)
  }

  const serverNow = () => Date.now() - skew

  function applyState(s) {
    if (!s) return
    state.value = s
    if (s.server_now) skew = Date.now() - Date.parse(s.server_now)
    maybeAutoResolve()
  }

  async function refresh() {
    try {
      applyState(await api.getState(roomCode, playerToken.value))
      error.value = ''
    } catch (e) {
      error.value = cleanErr(e)
    }
  }

  const round = computed(() => state.value?.round || null)

  const phase = computed(() => {
    tick.value // reactive dependency
    const s = state.value
    if (!s) return 'loading'
    if (s.status === 'Lobby') return 'lobby'
    if (s.status === 'Finished') return 'winner'
    const r = s.round
    if (!r) return 'lobby'
    const t = serverNow()
    if (t < Date.parse(r.started_at)) return 'reveal'
    if (t < Date.parse(r.deadline)) return 'select'
    return 'resolving'
  })

  const secondsLeft = computed(() => {
    tick.value
    const r = round.value
    if (!r) return 0
    const target =
      phase.value === 'reveal' ? Date.parse(r.started_at) : Date.parse(r.deadline)
    return Math.max(0, Math.ceil((target - serverNow()) / 1000))
  })

  function maybeAutoResolve() {
    const s = state.value
    if (!s || s.status !== 'Playing') return
    const r = s.round
    if (!r || r.resolved) return
    if (serverNow() >= Date.parse(r.deadline) && !resolving) {
      resolving = true
      api
        .resolveRound(roomCode)
        .then(applyState)
        .catch(() => {})
        .finally(() => {
          resolving = false
        })
    }
  }

  function start() {
    refresh()
    try {
      socket = initSocket()
      socket.on(`lss:${roomCode}`, applyState)
      socket.on(`lss:${roomCode}:reaction`, onReaction)
    } catch (e) {
      // realtime optional; poll covers it
    }
    pollTimer = setInterval(refresh, 2000)
    tickTimer = setInterval(() => {
      tick.value = Date.now()
      maybeAutoResolve()
    }, 200)
  }

  function stop() {
    if (socket) {
      socket.off(`lss:${roomCode}`, applyState)
      socket.off(`lss:${roomCode}:reaction`, onReaction)
      socket.disconnect()
    }
    clearInterval(pollTimer)
    clearInterval(tickTimer)
  }

  onUnmounted(stop)

  return {
    roomCode,
    state,
    error,
    phase,
    round,
    secondsLeft,
    playerToken,
    setToken,
    refresh,
    applyState,
    start,
    stop,
    serverNow,
    reactions,
    react,
  }
}

export function cleanErr(e) {
  let msg = e?.messages?.[0] || e?.message || String(e)
  // Strip Frappe's HTML / exception wrapping for a clean toast.
  msg = msg.replace(/<[^>]+>/g, '').trim()
  return msg || 'Something went wrong'
}
