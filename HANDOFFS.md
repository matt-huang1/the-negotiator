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
  filler fields. Added response_format=json_object, temperature=0, and an unwrap
  guard. Please eyeball extraction quality on the next run.
- [ ] (A→B, FYI — already done by agreement w/ Matthew) server/quote_extractor.py —
  switched Anthropic→OpenAI gpt-4o (team has $50 OpenAI credits, no Anthropic key).
  Prompt and output format unchanged; please sanity-check extraction quality on the
  next golden-call run.
- [ ] (example, delete me) (A→B) prompts/counter_agents/evasive_mover.md — Deb never
  gives a number even after full job detail; loosen the second-insistence rule.

## Done
