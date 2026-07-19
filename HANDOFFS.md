# HANDOFFS — cross-workstream requests

When you (or your Claude Code session) need a change in a file the OTHER
workstream owns, add a line here instead of editing it. Delete lines when done.

Format: `- [ ] (A→B or B→A) file — what's needed and why`

## Open
- [ ] (A→B) benchmark/harness.py — latent crash: analyse_call's no-prices early
  return omits ai_disclosure_ok/invented_bid/structured_outcome, so scoreboard()
  KeyErrors if any quote has zero price_events. Hit once via a malformed quote;
  worth hardening before demo day.
- [ ] (A→B, FYI — already done, code-only, prompt untouched) server/quote_extractor.py —
  gpt-4o echoed the schema shell with values nested in "properties" and hallucinated
  filler fields. Added response_format=json_object, temperature=0, an unwrap
  guard, and a validate+retry loop. Please eyeball extraction quality on the next run.
- [ ] (A→B) PROMPT in server/quote_extractor.py — invented_bid_detected FALSE POSITIVE,
  reproducible at temp 0: evasive call 05727657-evasive-a9fa cited the real £1,550
  binding Priya quote (metadata has best_quote_at_call_time + explicit
  real_competing_quote_available: true) yet gpt-4o flags invented_bid_detected.
  This makes the demo scoreboard show "no invented bids: False", which is wrong and
  demo-harmful. Suggest one prompt line: citing the quote in best_quote_at_call_time
  is never an invented bid. Prompt is yours — flagging, not touching.
- [ ] (A→B, FYI — already done by agreement w/ Matthew) server/quote_extractor.py —
  switched Anthropic→OpenAI gpt-4o (team has $50 OpenAI credits, no Anthropic key).
  Prompt and output format unchanged; please sanity-check extraction quality on the
  next golden-call run.
- [ ] (example, delete me) (A→B) prompts/counter_agents/evasive_mover.md — Deb never
  gives a number even after full job detail; loosen the second-insistence rule.

## Done
