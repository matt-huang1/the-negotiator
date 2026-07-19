# HANDOFFS — cross-workstream requests (hackathon artifact)

During the hackathon this file coordinated changes across the two workstreams
(see WORKSTREAMS.md). Kept for provenance; the project is no longer split.

## Known issues (open)
- benchmark/harness.py — `analyse_call`'s no-prices early return omits
  `ai_disclosure_ok` / `invented_bid` / `structured_outcome`, so `scoreboard()`
  raises KeyError if any quote has zero price_events. Doesn't affect the frozen
  golden set (all quotes have prices); harden before extending.

## Resolved during the hackathon
- quote_extractor switched Anthropic → OpenAI gpt-4o (team credits).
- gpt-4o schema-echo failures → JSON mode, temperature 0, validate+retry.
- invented_bid false positives → flag requires verbatim transcript evidence,
  verified in code against the transcript.
- aggressive persona now always asks the AI question once mid-negotiation.
