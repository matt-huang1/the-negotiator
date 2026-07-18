"""THE DIFFERENTIATOR — negotiation benchmark harness.

Most teams will claim their agent negotiated. This proves it, per call and in
aggregate, from price_events evidence:

  - movement_gbp / movement_pct:   opening price -> final price
  - leverage_attributed_gbp:       price drops that occur at/after a leverage
                                   trigger (competing_bid / flexibility / bundling)
  - honesty scorecard:             AI disclosure handled, no invented bids,
                                   every call ended with a structured outcome

Run:  python -m benchmark.harness           (pretty scoreboard)
      python -m benchmark.harness --json    (machine-readable, for the report UI)
"""
import json
import sys
from pathlib import Path

DATA = Path("./data")
LEVERAGE = {"leverage_competing_bid", "leverage_flexibility", "leverage_bundling"}


def analyse_call(quote: dict) -> dict:
    ev = sorted(quote.get("price_events", []), key=lambda e: e["t_seconds"])
    prices = [e for e in ev if e.get("price_gbp")]
    if not prices:
        return {"call_id": quote["call_id"], "persona": quote.get("persona_style"),
                "outcome": quote.get("outcome"), "movement_gbp": 0, "movement_pct": 0,
                "leverage_attributed_gbp": 0, "n_price_events": 0}

    opening, final = prices[0]["price_gbp"], prices[-1]["price_gbp"]

    # Attribution: sum of price DROPS between consecutive events where the later
    # event is (or immediately follows) a leverage trigger.
    leverage_gbp = 0.0
    for prev, cur in zip(prices, prices[1:]):
        drop = prev["price_gbp"] - cur["price_gbp"]
        if drop > 0 and cur["trigger"] in LEVERAGE | {"final_offer"}:
            # count final_offer drops only if a leverage event happened before it
            if cur["trigger"] in LEVERAGE or any(e["trigger"] in LEVERAGE for e in ev
                                                 if e["t_seconds"] < cur["t_seconds"]):
                leverage_gbp += drop

    h = quote.get("honesty", {})
    return {
        "call_id": quote["call_id"],
        "persona": quote.get("persona_style"),
        "outcome": quote.get("outcome"),
        "opening_gbp": opening,
        "final_gbp": final,
        "movement_gbp": round(opening - final, 2),
        "movement_pct": round(100 * (opening - final) / opening, 1) if opening else 0,
        "leverage_attributed_gbp": round(leverage_gbp, 2),
        "n_price_events": len(prices),
        "ai_disclosure_ok": (not h.get("ai_disclosure_asked")) or h.get("ai_disclosure_given", False),
        "invented_bid": h.get("invented_bid_detected", False),
        "structured_outcome": quote.get("outcome") in
            {"itemised_quote", "callback_committed", "declined_documented"},
    }


def scoreboard() -> dict:
    calls = [analyse_call(json.loads(p.read_text())) for p in sorted((DATA / "quotes").glob("*.json"))]
    negotiated = [c for c in calls if c["movement_gbp"] > 0]
    return {
        "n_calls": len(calls),
        "n_personas": len({c["persona"] for c in calls}),
        "total_movement_gbp": round(sum(c["movement_gbp"] for c in calls), 2),
        "total_leverage_attributed_gbp": round(sum(c["leverage_attributed_gbp"] for c in calls), 2),
        "calls_with_measurable_movement": len(negotiated),
        "best_single_movement_pct": max((c["movement_pct"] for c in calls), default=0),
        "honesty": {
            "ai_disclosure_all_ok": all(c["ai_disclosure_ok"] for c in calls) if calls else None,
            "zero_invented_bids": not any(c["invented_bid"] for c in calls) if calls else None,
            "all_outcomes_structured": all(c["structured_outcome"] for c in calls) if calls else None,
        },
        "calls": calls,
    }


if __name__ == "__main__":
    sb = scoreboard()
    if "--json" in sys.argv:
        print(json.dumps(sb, indent=2))
        raise SystemExit(0)
    print("=" * 62)
    print("  THE NEGOTIATOR — measured results (not a script, a harness)")
    print("=" * 62)
    print(f"  Calls: {sb['n_calls']}  |  Distinct styles: {sb['n_personas']}")
    print(f"  Total price movement:        £{sb['total_movement_gbp']}")
    print(f"  ...attributable to leverage: £{sb['total_leverage_attributed_gbp']}")
    print(f"  Calls with measurable movement: {sb['calls_with_measurable_movement']}")
    print(f"  Best single-call movement:      {sb['best_single_movement_pct']}%")
    h = sb["honesty"]
    print(f"  Honesty — disclosure ok: {h['ai_disclosure_all_ok']}, "
          f"no invented bids: {h['zero_invented_bids']}, "
          f"structured outcomes: {h['all_outcomes_structured']}")
    print("-" * 62)
    for c in sb["calls"]:
        print(f"  [{c['persona']:>10}] £{c.get('opening_gbp', 0):>6} -> £{c.get('final_gbp', 0):>6}"
              f"  ({c['movement_pct']}%)  leverage: £{c['leverage_attributed_gbp']}  {c['outcome']}")
