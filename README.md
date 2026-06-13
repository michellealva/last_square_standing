# Last Square Standing

A real-time multiplayer elimination party game, built as a [Frappe](https://frappeframework.com) app with a Vue 3 + Vite + Tailwind frontend.

Each round every player secretly taps one tile on a shrinking grid. Tiles two or more players land on **explode** (those players are out); lone tiles survive. The grid shrinks 5×5 → 4×4 → 3×3 → 2×2 each round until one player is left. On the final 2×2 grid, if no one collides, the **slowest to lock in** is eliminated. Installable as a PWA.

## Features
- Anonymous play — no login; players are tracked by a browser token. 3–10 per room.
- Server-authoritative engine (timing, resolution, scoring all validated server-side).
- Real-time updates via Frappe socket.io, with a polling fallback.
- Themed rounds — each round shows a category prompt and a word on every tile.
- Cumulative cross-game leaderboard.
- Instant rematch ("Play Again") and lobby reset, keeping the same room.
- Juice: haptics, sound (mute toggle), countdown tension, collision explosions, winner confetti — all respecting `prefers-reduced-motion`.
- PWA: installable, full-screen standalone, offline app shell.

## Tech
- **Backend:** `last_square_standing/api.py` (whitelisted, guest-allowed API), DocTypes `LSS Room`, `LSS Room Player`, `LSS Round`, `LSS Selection`, `LSS Leaderboard`. Word bank in `last_square_standing/words.py`.
- **Frontend:** `frontend/` — Vue 3, vue-router, frappe-ui, Tailwind. Served at `/lss` (SPA, history mode) via `website_route_rules` in `hooks.py`.
- **Engine smoke test:** `last_square_standing/sim.py` — headless end-to-end check.

## Local development
Requires a working [bench](https://github.com/frappe/bench) and **Node ≥ 24**.

```bash
# from your bench directory
bench get-app https://github.com/michellealva/last_square_standing
bench --site <your-site> install-app last_square_standing
bench --site <your-site> migrate

# frontend
cd apps/last_square_standing/frontend
yarn install
yarn build            # outputs the SPA to ../last_square_standing/www/lss.html + public/frontend
                      # (use `yarn dev` for hot-reload during development)

bench --site <your-site> clear-website-cache
```

Run the engine smoke test:

```bash
bench --site <your-site> execute last_square_standing.sim.run
```

Play at `http://<your-site>:8000/lss/`.

## Deploy
The built frontend is **not** committed (see `.gitignore`); build it on the server:

```bash
bench get-app https://github.com/michellealva/last_square_standing   # private repo: configure a deploy key / token
bench --site <site> install-app last_square_standing
bench --site <site> migrate
cd apps/last_square_standing/frontend && yarn install && yarn build
bench --site <site> clear-website-cache
bench build
```

> PWA install requires a secure context — serve the site over **HTTPS** in production.
> After every frontend rebuild, run `bench --site <site> clear-website-cache` so clients pick up the new bundle.

## License
MIT
