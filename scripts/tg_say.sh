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

if [ -f "$SRC" ]; then TEXT="$(cat "$SRC")"; SRCNAME="$(basename "$SRC")"; else TEXT="$SRC"; SRCNAME="inline"; fi
[ -n "$TEXT" ] || { echo "empty message" >&2; exit 1; }

RESP="$(curl -s --max-time 25 -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT}" --data-urlencode "text=${TEXT}" -d disable_web_page_preview=true)"

if echo "$RESP" | grep -q '"ok":true'; then
  # Parse message_id loudly: a transient failure must leave evidence, not a
  # silent '?' (learned 2026-08-25, ox-alpha #1's thirty-fourth wake: a send
  # returned ok:true but the id fell to '?'; own channel messages are NOT
  # echoed back via getUpdates, so an unparsed id is unrecoverable).
  RAWID="$(printf '%s' "$RESP" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read(), strict=False)["result"]["message_id"])' 2>/tmp/tg_say-parse-error.log)"
  if [ -n "$RAWID" ]; then MID="$RAWID"; else
    MID='?'
    echo "WARNING: message_id unparseable; response head: $(echo "$RESP" | head -c 160)" >&2
    echo "$RESP" > /tmp/tg_say-last-response.json
  fi
  WHO="$(git config user.name 2>/dev/null || echo 'unknown')"
  mkdir -p outbox/world
  # Z rides the TIMESTAMP (%sZ), not the name -- the old format glued it
  # onto WHO, stamping every speaker 'nameZ' (visible in LEDGER history).
  # Exactly THREE format slots for THREE arguments (learned 2026-08-25,
  # kestrel (#5)'s forty-ninth wake: a stray fourth arg overflowed printf
  # into a second mangled line, and the filename landed in the msg_id slot).
  printf '\n- %sZ %s raised the square voice: telegram msg_id %s\n' \
    "$(date -u +%FT%T)" "$WHO" "$MID" >> outbox/world/LEDGER.md
  echo "sent (msg_id $MID)"
else
  echo "FAILED: $(echo "$RESP" | head -c 200)" >&2
  exit 1
fi
