/* Service worker for the Last Square Standing PWA.
 *
 * Served from the site root (/lss-sw.js) but registered with scope "/lss/", so it
 * only ever controls the game — never the rest of the Frappe site.
 *
 * Strategy:
 *   - navigations (the /lss/ shell): network-first, fall back to the cached shell
 *     when offline. This means a fresh build is always picked up while online, so
 *     there is no stale-bundle problem.
 *   - hashed build assets (/assets/last_square_standing/frontend/...): cache-first
 *     (filenames are content-hashed, so they're immutable).
 *   - everything else (especially /api/ game calls and realtime): passthrough,
 *     never cached — the game is server-authoritative and must not be stale.
 */

const CACHE = 'lss-v1'
const ASSET_PREFIX = '/assets/last_square_standing/frontend/'

self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys()
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      await self.clients.claim()
    })()
  )
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  if (req.method !== 'GET') return

  const url = new URL(req.url)
  if (url.origin !== self.location.origin) return

  // App shell — always try the network so new builds load; cache as fallback.
  if (req.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          const fresh = await fetch(req)
          const cache = await caches.open(CACHE)
          cache.put('/lss/shell', fresh.clone())
          return fresh
        } catch (e) {
          const cached = await caches.match('/lss/shell')
          return cached || Response.error()
        }
      })()
    )
    return
  }

  // Immutable hashed assets — cache-first.
  if (url.pathname.startsWith(ASSET_PREFIX)) {
    event.respondWith(
      (async () => {
        const cached = await caches.match(req)
        if (cached) return cached
        const fresh = await fetch(req)
        if (fresh && fresh.ok) {
          const cache = await caches.open(CACHE)
          cache.put(req, fresh.clone())
        }
        return fresh
      })()
    )
  }
  // Anything else (api, realtime, etc.) falls through to the network untouched.
})
