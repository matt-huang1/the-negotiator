# Known issues

- `benchmark/harness.py` — `analyse_call`'s early return for quotes with zero
  price events omits `ai_disclosure_ok` / `invented_bid` / `structured_outcome`,
  so `scoreboard()` raises KeyError if such a quote is present. The frozen
  golden set is unaffected (every quote has prices); harden before extending.
