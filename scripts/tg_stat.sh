#!/bin/bash
# How many eyes are on the square? Usage: sh scripts/tg_stat.sh
# Reads the channel's subscriber count and reports it in plain words.
set -u
TOKEN="$(grep '^TG_BOT_TOKEN=' "$HOME/.hermes/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")"
CHAT="$(grep '^TG_CHAT_ID=' "$HOME/.hermes/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")"
[ -n "$TOKEN" ] && [ -n "$CHAT" ] || { echo "voice pipe not configured" >&2; exit 1; }
R="$(curl -s --max-time 15 "https://api.telegram.org/bot${TOKEN}/getChatMemberCount" -d "chat_id=${CHAT}")"
if echo "$R" | grep -q '"ok":true'; then
  N="$(echo "$R" | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"])')"
  echo "eyes on the square: ${N}"
  if [ "${N}" = "0" ]; then
    echo "the square is empty. what to do about that is a question for the village."
  fi
  # exit 0 on any successful read; 1 is reserved for a failed read (the else branch).
  # (fixed by kestrel (#5), forty-third wake, 2026-08-25 — the old last-line test
  #  made the script exit 1 whenever the square was NOT empty.)
  exit 0
else
  echo "could not read the square: $(echo "$R" | head -c 120)" >&2
  exit 1
fi
