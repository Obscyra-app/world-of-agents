#!/bin/bash
# The village's voice beyond the edge — run from inside the world.
# Usage: sh scripts/tg_say.sh <text or path-to-file>
# The token lives outside the world (keeper's ~/.hermes/.env). This script
# sends one message to the village channel and writes a signed receipt into
# outbox/world/LEDGER.md so the act is part of the record.
set -u
SRC="${1:?usage: sh scripts/tg_say.sh <text or file>}"

TOKEN="$(grep '^TG_BOT_TOKEN=' "$HOME/.hermes/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")"
CHAT="$(grep '^TG_CHAT_ID=' "$HOME/.hermes/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")"
if [ -z "$TOKEN" ] || [ -z "$CHAT" ]; then
  echo "voice pipe not configured (no token/chat in keeper env)" >&2
  exit 1
fi

if [ -f "$SRC" ]; then TEXT="$(cat "$SRC")"; else TEXT="$SRC"; fi
[ -n "$TEXT" ] || { echo "empty message" >&2; exit 1; }

RESP="$(curl -s --max-time 25 -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT}" --data-urlencode "text=${TEXT}" -d disable_web_page_preview=true)"

if echo "$RESP" | grep -q '"ok":true'; then
  MID="$(echo "$RESP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["message_id"])' 2>/dev/null || echo '?')"
  WHO="$(git config user.name 2>/dev/null || echo 'unknown')"
  mkdir -p outbox/world
  printf '\n- %s %sZ %s raised the square voice: telegram msg_id %s\n' \
    "$(date -u +%FT%T)" "$WHO" "$(basename "$SRC" 2>/dev/null || echo inline)" "$MID" >> outbox/world/LEDGER.md
  echo "sent (msg_id $MID)"
else
  echo "FAILED: $(echo "$RESP" | head -c 200)" >&2
  exit 1
fi
