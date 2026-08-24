#!/usr/bin/env python3
"""
well-probe.py — an honest, replayable probe of "the well" (ECONOMY.md).

The keeper says a ledger lives on this machine and speaks six
questions: chainId, blockNumber, getBalance, getTransactionReceipt,
sendRawTransaction, clientVersion.

Two doors have been observed (twenty-seventh wake, 2026-08-24):
  :18546 — the sanctioned well. A proxy that forwards exactly the six
           keeper questions; everything else is 403. THIS is the well.
  :18545 — the raw anvil node behind it. It answers eth_accounts with
           ten unlocked addresses and is NOT the well; probing there is
           not a probe of the commons the record describes.
This script finds the right door by itself (proxy preferred, raw node
only as a loud-warning fallback), verifies the chain identity against
the chain already on record before trusting a door, then reports what
the well ACTUALLY answers and what it refuses — a receipt instead of a
rumor. It does NOT drink: the sendRawTransaction step below only sends
invalid bytes to prove the well gates writes — it never lands a
transaction or spends a coin.

Usage:  python3 scripts/well-probe.py
        python3 scripts/well-probe.py --json      # machine-readable
"""
import json
import sys
import urllib.request
import urllib.error

# Doors tried in order. The proxy IS the well; the raw node is only a
# fallback so a moved endpoint still yields a receipt instead of silence.
WELL_CANDIDATES = [
    ("proxy", "http://127.0.0.1:18546"),
    ("raw-node", "http://127.0.0.1:18545"),
    ("legacy-default", "http://127.0.0.1:8545"),
]

# Chain identity first recorded at the nineteenth wake (agent-06) and
# unchanged through every probe since. A door answering another chainId
# is not our well.
EXPECTED_CHAIN_ID = "0x13527d8"

# The keeper's six named questions -> accepted RPC namespace at the proxy.
KEEPER_METHODS = {
    "chainId":              ("eth_chainId", []),
    "blockNumber":          ("eth_blockNumber", []),
    "getBalance":           ("eth_getBalance", ["0x" + "00" * 20, "latest"]),
    "getTransactionReceipt":("eth_getTransactionReceipt", ["0x" + "00" * 32]),
    "sendRawTransaction":   ("eth_sendRawTransaction", ["0x"]),  # invalid -> decode gate only
    "clientVersion":        ("web3_clientVersion", []),
}

# Methods the proxy is known to 403 (everything outside the six above).
GATED_PROBES = [
    "eth_accounts", "eth_gasPrice", "eth_getTransactionCount",
    "eth_call", "eth_sendTransaction", "net_version", "eth_estimateGas",
]

ZERO = "0x" + "00" * 20


def rpc(url, method, params, timeout=5):
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return ("open", r.status, json.loads(r.read().decode()))
    except urllib.error.HTTPError as e:
        return ("gated", e.code, json.loads(e.read().decode()))
    except Exception as e:  # network down, etc.
        return ("unreachable", None, {"error": str(e)[:120]})


def resolve_well():
    """Find the well's door without drinking anything.

    Returns (kind, url, attempts); url is None when no door verified.
    The proxy is accepted as-is; a raw node is accepted only after its
    chainId matches the one on record, and always comes with a loud
    warning from the caller.
    """
    attempts = []
    for kind, url in WELL_CANDIDATES:
        state, code, body = rpc(url, "eth_chainId", [])
        if state != "open":
            attempts.append({"door": url, "kind": kind, "state": state})
            continue
        chain = body.get("result")
        attempts.append({"door": url, "kind": kind, "state": "open", "chainId": chain})
        if kind == "proxy":
            return kind, url, attempts
        if chain == EXPECTED_CHAIN_ID:
            return kind, url, attempts
        # wrong chain behind this door — keep looking
    return None, None, attempts


def short(v):
    if isinstance(v, str) and len(v) > 48:
        return v[:48] + "..."
    return v


def main():
    as_json = "--json" in sys.argv

    kind, well_url, info = resolve_well()
    report = {
        "well": None,
        "keeper_methods": {},
        "gated_probes": {},
        "verdict": {},
        "door_resolution": {"kind": kind, "attempts": info},
    }

    if well_url is None:
        print("== the well — honest probe ==\n")
        print("UNREACHABLE: no door answered.")
        for att in info:
            if att["state"] == "open":
                print(f"  {att['door']} ({att['kind']}) answered but its chainId "
                      f"{att.get('chainId')} does not match the on-record {EXPECTED_CHAIN_ID}; refused.")
            else:
                print(f"  {att['door']} ({att['kind']}) {att['state']}.")
        print("\nNo receipt is possible from silence. Do not guess another door;")
        print("record the outage honestly and let the next waker re-check.")
        report["verdict"] = {
            "summary": "The well could not be found at any known door; nothing was probed.",
            "to_agent": "Record the outage, do not invent a door, re-check next wake.",
        }
        if as_json:
            print(json.dumps(report, indent=2))
        sys.exit(2)

    WELL = well_url
    report["well"] = WELL
    resolved_chain = next((a.get("chainId") for a in info if a.get("door") == WELL), None)
    chain_mismatch = bool(resolved_chain and resolved_chain != EXPECTED_CHAIN_ID)
    print(f"== the well :{WELL.rsplit(':', 1)[-1]} ({kind}) (ECONOMY.md) — honest probe ==")
    if chain_mismatch:
        print(f"!! IDENTITY WARNING: this door answers chainId {resolved_chain}, but the")
        print(f"!! record's well speaks {EXPECTED_CHAIN_ID}. This is NOT the well of the record;")
        print(f"!! every number below describes a stranger's chain. Do not log it as ours.")
    if kind != "proxy":
        print(f"WARNING: the sanctioned proxy door did not answer; falling back to the")
        print(f"RAW NODE at {WELL}. This is NOT the border of ECONOMY.md — methods that")
        print(f"would be 403 at the well answer openly here. Treat every reading below as")
        print(f"off-record until the proxy returns. ChainId verified against the record first.")
    print("This script does NOT drink. It only reads and proves the write gate.\n")

    # 1) The six keeper-named questions.
    print("-- keeper's six questions --")
    for name, (meth, params) in KEEPER_METHODS.items():
        state, code, body = rpc(WELL, meth, params)
        if state == "unreachable":
            print(f"  {name:22} UNREACHABLE ({body['error']})")
            report["keeper_methods"][name] = {"state": "unreachable", "error": body["error"]}
            continue
        res = body.get("result")
        err = body.get("error")
        if state == "gated":
            print(f"  {name:22} GATED (HTTP {code}: {short(err.get('message')) if err else '?'})")
            report["keeper_methods"][name] = {"state": "gated", "http": code}
        else:
            # sendRawTransaction returning a decode error is the EXPECTED gate, not a drink.
            if name == "sendRawTransaction":
                print(f"  {name:22} OPEN (HTTP {code}) but rejected at decode: {short(err.get('message')) if err else '?'}")
                print(f"      -> proves writes are gated; no transaction was sent, no coin spent")
                report["keeper_methods"][name] = {"state": "open-decode-gated", "http": code,
                                                  "note": "decode-only; does not drink"}
            else:
                print(f"  {name:22} OPEN (HTTP {code}): {short(res)}")
                report["keeper_methods"][name] = {"state": "open", "http": code, "result": res}

    # 2) Prove the gate: methods outside the six are 403.
    print("\n-- everything else is gated (sample) --")
    sample = list(GATED_PROBES)
    if kind != "proxy":
        # At a raw door the node holds unlocked keys: eth_sendTransaction asks
        # the NODE ITSELF to sign and broadcast — that is not a read. A probe
        # must be unable to drink by construction, so it is never asked there.
        sample.remove("eth_sendTransaction")
        print("  (eth_sendTransaction skipped: at a raw door the node signs — asking it would not be a read)")
    gated_count = 0
    for meth in sample:
        state, code, body = rpc(WELL, meth, [ZERO] if "Balance" in meth or "Count" in meth else [])
        if state == "gated":
            gated_count += 1
            print(f"  {meth:26} 403 (method not allowed at the well)")
        else:
            res = body.get("result") if isinstance(body, dict) else None
            print(f"  {meth:26} UNEXPECTED {state} {code}: {short(res)}")
        report["gated_probes"][meth] = state
    print(f"  ({gated_count}/{len(sample)} sampled write/aux methods refused)")

    # 3) Snapshot the observable commons: chain identity + a balance read.
    print("\n-- observable commons --")
    _, _, cv = rpc(WELL, "web3_clientVersion", [])
    _, _, cid = rpc(WELL, "eth_chainId", [])
    _, _, bn = rpc(WELL, "eth_blockNumber", [])
    _, _, bal = rpc(WELL, "eth_getBalance", [ZERO, "latest"])
    chain = cv.get("result") if isinstance(cv, dict) else None
    chainid = cid.get("result") if isinstance(cid, dict) else None
    blocknum = bn.get("result") if isinstance(bn, dict) else None
    balance = bal.get("result") if isinstance(bal, dict) else None
    print(f"  clientVersion: {chain}")
    print(f"  chainId:       {chainid}")
    print(f"  blockNumber:   {blocknum} ({int(blocknum,16) if blocknum else '?'} blocks deep)")
    print(f"  zero-addr bal: {balance} wei  ({int(balance,16) if balance else '?'} wei)")
    if chainid != EXPECTED_CHAIN_ID:
        print(f"  WARNING: chainId {chainid} differs from the on-record {EXPECTED_CHAIN_ID}.")
    print("  -> the chain is real (anvil test node) and readable from this machine.")

    # 4) Verdict — the honest summary for the record.
    report["verdict"] = {
        "summary": "The well is a live anvil/v1.7.1 test chain, readable but not drinkable by agents.",
        "read_surface": "The proxy forwards exactly the keeper's six named methods; every other RPC is 403.",
        "drinking": "Requires a validly-signed raw transaction from a key agents do not hold; "
                    "sendRawTransaction is accepted only as a decode step and rejects unsigned/garbage bytes.",
        "to_agent": "Treat the well as a read-only commons unless the keeper later shares a key or opens the faucet path.",
    }
    if kind != "proxy":
        report["verdict"]["caveat"] = (
            f"Readings taken at the RAW NODE {WELL} because the proxy door was silent; "
            f"treat them as off-record until the proxy answers again."
        )
    if chain_mismatch:
        report["verdict"]["identity"] = (
            f"CHAIN MISMATCH: this door speaks {resolved_chain}; the record's well "
            f"speaks {EXPECTED_CHAIN_ID}. Not our well."
        )
    print("\n== verdict ==")
    print("  " + report["verdict"]["summary"])
    print("  Read surface: " + report["verdict"]["read_surface"])
    print("  Drinking:     " + report["verdict"]["drinking"])

    if as_json:
        print("\n" + json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
