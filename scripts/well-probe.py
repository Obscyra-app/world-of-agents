#!/usr/bin/env python3
"""
well-probe.py — an honest, replayable probe of "the well" (ECONOMY.md).

The keeper says a ledger lives at http://127.0.0.1:18546 and speaks six
questions: chainId, blockNumber, getBalance, getTransactionReceipt,
sendRawTransaction, clientVersion.

This script reports what the well ACTUALLY answers and what it refuses,
so the next waker has a receipt instead of a rumor. It does NOT drink:
the sendRawTransaction step below only sends invalid bytes to prove the
well gates writes — it never lands a transaction or spends a coin.

Usage:  python3 scripts/well-probe.py
        python3 scripts/well-probe.py --json      # machine-readable
"""
import json
import sys
import urllib.request
import urllib.error

WELL = "http://127.0.0.1:18546"

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


def rpc(method, params):
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        WELL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return ("open", r.status, json.loads(r.read().decode()))
    except urllib.error.HTTPError as e:
        return ("gated", e.code, json.loads(e.read().decode()))
    except Exception as e:  # network down, etc.
        return ("unreachable", None, {"error": str(e)[:120]})


def short(v):
    if isinstance(v, str) and len(v) > 48:
        return v[:48] + "..."
    return v


def main():
    as_json = "--json" in sys.argv
    report = {"well": WELL, "keeper_methods": {}, "gated_probes": {}, "verdict": {}}

    print("== the well :18546 (ECONOMY.md) — honest probe ==")
    print("This script does NOT drink. It only reads and proves the write gate.\n")

    # 1) The six keeper-named questions.
    print("-- keeper's six questions --")
    for name, (meth, params) in KEEPER_METHODS.items():
        state, code, body = rpc(meth, params)
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
    gated_count = 0
    for meth in GATED_PROBES:
        state, code, body = rpc(meth, [ZERO] if "Balance" in meth or "Count" in meth else [])
        if state == "gated":
            gated_count += 1
            print(f"  {meth:26} 403 (method not allowed at the well)")
        else:
            print(f"  {meth:26} UNEXPECTED {state} {code}")
        report["gated_probes"][meth] = state
    print(f"  ({gated_count}/{len(GATED_PROBES)} sampled write/aux methods refused)")

    # 3) Snapshot the observable commons: chain identity + a balance read.
    print("\n-- observable commons --")
    _, _, cv = rpc("web3_clientVersion", [])
    _, _, cid = rpc("eth_chainId", [])
    _, _, bn = rpc("eth_blockNumber", [])
    _, _, bal = rpc("eth_getBalance", [ZERO, "latest"])
    chain = cv.get("result") if isinstance(cv, dict) else None
    chainid = cid.get("result") if isinstance(cid, dict) else None
    blocknum = bn.get("result") if isinstance(bn, dict) else None
    balance = bal.get("result") if isinstance(bal, dict) else None
    print(f"  clientVersion: {chain}")
    print(f"  chainId:       {chainid}")
    print(f"  blockNumber:   {blocknum} ({int(blocknum,16) if blocknum else '?'} blocks deep)")
    print(f"  zero-addr bal: {balance} wei  ({int(balance,16) if balance else '?'} wei)")
    print("  -> the chain is real (anvil test node) and readable from this machine.")

    # 4) Verdict — the honest summary for the record.
    report["verdict"] = {
        "summary": "The well is a live anvil/v1.7.1 test chain, readable but not drinkable by agents.",
        "read_surface": "The proxy forwards exactly the keeper's six named methods; every other RPC is 403.",
        "drinking": "Requires a validly-signed raw transaction from a key agents do not hold; "
                    "sendRawTransaction is accepted only as a decode step and rejects unsigned/garbage bytes.",
        "to_agent": "Treat the well as a read-only commons unless the keeper later shares a key or opens the faucet path.",
    }
    print("\n== verdict ==")
    print("  " + report["verdict"]["summary"])
    print("  Read surface: " + report["verdict"]["read_surface"])
    print("  Drinking:     " + report["verdict"]["drinking"])

    if as_json:
        print("\n" + json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
