import { ref } from 'vue'

/**
 * Dependency-free sound effects, synthesized with the Web Audio API — no asset
 * files, works offline. The AudioContext is created lazily and resumed on the
 * first user gesture (browser autoplay policy), so sound only kicks in after the
 * first tap. Everything no-ops while muted.
 */

export const muted = ref(localStorage.getItem('lss_muted') === '1')

export function toggleMute() {
  muted.value = !muted.value
  localStorage.setItem('lss_muted', muted.value ? '1' : '0')
}

let ctx = null

function ac() {
  if (typeof window === 'undefined') return null
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return null
    ctx = new AC()
  }
  if (ctx.state === 'suspended') ctx.resume()
  return ctx
}

// A single shaped oscillator note.
function tone({ freq = 440, type = 'sine', start = 0, dur = 0.15, gain = 0.2, glide = null }) {
  const c = ac()
  if (!c) return
  const t0 = c.currentTime + start
  const osc = c.createOscillator()
  const g = c.createGain()
  osc.type = type
  osc.frequency.setValueAtTime(freq, t0)
  if (glide) osc.frequency.exponentialRampToValueAtTime(glide, t0 + dur)
  g.gain.setValueAtTime(0.0001, t0)
  g.gain.exponentialRampToValueAtTime(gain, t0 + 0.01)
  g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur)
  osc.connect(g).connect(c.destination)
  osc.start(t0)
  osc.stop(t0 + dur + 0.02)
}

// A short burst of filtered noise — used for the explosion.
function noise({ dur = 0.4, gain = 0.35 }) {
  const c = ac()
  if (!c) return
  const frames = Math.floor(c.sampleRate * dur)
  const buf = c.createBuffer(1, frames, c.sampleRate)
  const data = buf.getChannelData(0)
  for (let i = 0; i < frames; i++) {
    // decaying white noise
    data[i] = (Math.random() * 2 - 1) * (1 - i / frames)
  }
  const src = c.createBufferSource()
  src.buffer = buf
  const lp = c.createBiquadFilter()
  lp.type = 'lowpass'
  lp.frequency.setValueAtTime(1200, c.currentTime)
  lp.frequency.exponentialRampToValueAtTime(200, c.currentTime + dur)
  const g = c.createGain()
  g.gain.setValueAtTime(gain, c.currentTime)
  g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur)
  src.connect(lp).connect(g).connect(c.destination)
  src.start()
}

export function playPick() {
  if (muted.value) return
  tone({ freq: 660, type: 'triangle', dur: 0.08, gain: 0.15 })
}

export function playTick() {
  if (muted.value) return
  tone({ freq: 880, type: 'square', dur: 0.06, gain: 0.12 })
}

export function playExplosion() {
  if (muted.value) return
  noise({ dur: 0.45, gain: 0.35 })
  tone({ freq: 180, type: 'sawtooth', dur: 0.35, gain: 0.25, glide: 60 })
}

export function playWin() {
  if (muted.value) return
  // rising major arpeggio
  const notes = [523.25, 659.25, 783.99, 1046.5]
  notes.forEach((f, i) => tone({ freq: f, type: 'triangle', start: i * 0.12, dur: 0.22, gain: 0.2 }))
}
