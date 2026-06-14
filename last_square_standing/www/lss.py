# Never cache the SPA shell: the page bakes in a per-session CSRF token (via
# Frappe's `<!-- csrf_token -->` replacement), so a cached copy would hand one
# session's token to another. We intentionally do NOT generate a token here —
# anonymous guests share the "Guest" session, and a token only needs to be sent
# back when the session already has one (e.g. a logged-in tab in the same browser).
no_cache = 1
