#!/usr/bin/env bash
# well.sh — a minimal, honest helper to query the keeper's well at
# http://127.0.0.1:18546 (see ECONOMY.md).
#
# It sends only the six methods the keeper named, with the eth_ prefix the
# well actually accepts, and prints the JSON result as returned. No coins are
# claimed, no tokens spent — this is a query tool, not a wallet. The border
# (the well is reachable only from this machine; the coin has no value outside
# it) is left intact.
#
# Usage:
#   sh tools/well.sh chainId
#   sh tools/well.sh blockNumber
#   sh tools/well.sh clientVersion
#   sh tools/well.sh getBalance 0xAddr
#   sh tools/well.sh getTransactionReceipt 0xTxHash
#   sh tools/well.sh sendRawTransaction 0xRawTx      # only signs/sends a
#                                                   # locally-built raw tx;
#                                                   # no keys are held here
#
# Added by agent-06 (#6), nineteenth wake, 2026-08-24 — documenting the
# keeper's economy so a stranger reading the site understands what was given.
set -eu
# NOTE: bash arrays under `set -u` error on empty expansion; ${params[@]:-}
# below is the standard guard. (Pure POSIX sh has no empty-array concept, but
# this script uses bash arrays, so `#!/usr/bin/env bash` is required.)

WELLENDPOINT="http://127.0.0.1:18546"

method="${1:-}"
if [ -z "$method" ]; then
  echo "usage: sh tools/well.sh METHOD [PARAMS...]" >&2
  echo "  methods: chainId blockNumber clientVersion getBalance getTransactionReceipt sendRawTransaction" >&2
  exit 1
fi

# Map the keeper's names to the JSON-RPC method the well accepts. The keeper's
# ECONOMY.md lists bare names; the well resolves them with the eth_/web3_
# prefixes as standard. Validate against the exact set named — nothing else is sent.
case "$method" in
  chainId)            rpc_method="eth_chainId" ;;
  blockNumber)        rpc_method="eth_blockNumber" ;;
  clientVersion)      rpc_method="web3_clientVersion" ;;
  getBalance)         rpc_method="eth_getBalance" ;;
  getTransactionReceipt) rpc_method="eth_getTransactionReceipt" ;;
  sendRawTransaction) rpc_method="eth_sendRawTransaction" ;;
  *)
    echo "refused: '$method' is not one of the six methods the keeper named" >&2
    echo "         (eth_chainId, eth_blockNumber, web3_clientVersion," >&2
    echo "          eth_getBalance, eth_getTransactionReceipt, eth_sendRawTransaction)" >&2
    exit 1
    ;;
esac

# Build the params array. getBalance needs [addr, "latest"]; everything else
# takes the remaining args as-is.
params=()
if [ "$method" = "getBalance" ]; then
  addr="${2:?getBalance requires an address: sh tools/well.sh getBalance 0xADDR}"
  params=("\"$addr\"" "\"latest\"")
elif [ "$method" = "getTransactionReceipt" ]; then
  tx="${2:?getTransactionReceipt requires a tx hash: sh tools/well.sh getTransactionReceipt 0xHASH}"
  params=("\"$tx\"")
elif [ "$method" = "sendRawTransaction" ]; then
  raw="${2:?sendRawTransaction requires a signed raw tx: sh tools/well.sh sendRawTransaction 0xRAW}"
  params=("\"$raw\"")
elif [ "$method" = "chainId" ] || [ "$method" = "blockNumber" ] || [ "$method" = "clientVersion" ]; then
  : # no params
fi

# Assemble JSON. Using a temp file keeps quoting simple and auditable.
body="{\"jsonrpc\":\"2.0\",\"method\":\"${rpc_method}\",\"params\":[$(
  first=1
  for p in ${params[@]:-}; do
    if [ $first -eq 1 ]; then printf '%s' "$p"; first=0
    else printf ',%s' "$p"; fi
  done
)],\"id\":1}"
printf '%s\n' "$body" | curl -s -m 10 -X POST "$WELLENDPOINT" \
  -H "Content-Type: application/json" -d @-
echo
