"""Red-flag detection vs market benchmarks.

Brief: a price 30%+ below market signals a suspicious lowball, not a win.
Benchmarks below are seed values for a 2-bed London move — replace/extend with
moveBuddha / FMCSA-derived bands and cite the source in the report.
"""
BENCHMARKS = {
    "moving_2bed_london": {"low": 900, "median": 1400, "high": 2100, "source": "seed — replace with moveBuddha/FMCSA data"},
}

LOWBALL_THRESHOLD = 0.30


def flags_for(total_gbp: float, itemised: list[dict], benchmark_key: str = "moving_2bed_london") -> list[str]:
    b = BENCHMARKS[benchmark_key]
    flags = []
    if total_gbp < b["median"] * (1 - LOWBALL_THRESHOLD):
        flags.append(f"LOWBALL: £{total_gbp:.0f} is >30% below market median £{b['median']} — "
                     "sight-unseen lowballs are 40% more likely to end above quote (FMCSA)")
    if total_gbp > b["high"]:
        flags.append(f"ABOVE MARKET: £{total_gbp:.0f} exceeds typical high band £{b['high']}")
    if not itemised:
        flags.append("NO ITEMISATION: total given without a breakdown — final-bill risk")
    conditional = [f["label"] for f in itemised or [] if f.get("conditional")]
    if conditional:
        flags.append(f"CONDITIONAL FEES: {', '.join(conditional)} — could inflate final bill")
    return flags
