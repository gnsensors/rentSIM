#!/bin/sh
# Runs at container startup via /docker-entrypoint.d — writes runtime config
# into a JS file that index.html loads before the React bundle.
cat > /usr/share/nginx/html/env-config.js << EOF
window.__API_URL__ = "${VITE_API_URL}";
window.__WS_URL__  = "${VITE_WS_URL}";
EOF
