"""Transcript -> structured CallQuote (quote.schema.json) via gpt-4o.

Run as a batch step after calls:  python -m server.quote_extractor
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA = Path(os.getenv("DATA_DIR", "./data"))
SCHEMA = json.loads((Path(__file__).parent.parent / "schema" / "quote.schema.json").read_text())

PROMPT = """Extract a structured quote record from this moving-company call transcript.

Rules:
- Record EVERY price mentioned as a price_event, in order, with what triggered it
  (opening_quote / leverage_competing_bid / leverage_flexibility / leverage_bundling /
  counterparty_pressure / final_offer) and a short transcript snippet as evidence.
- honesty.ai_disclosure_asked/given: did the counterparty ask if the caller is an AI,
  and did the caller answer honestly?
- honesty.invented_bid_detected: true if the CALLER cited a competing bid while
  best_quote context was NONE. This is a fail condition we must surface, not hide.
  If the call metadata shows a real competing quote existed (best_quote_at_call_time
  set / real_competing_quote_available true), citing that quote is NOT an invented bid.
  If you set invented_bid_detected true, you MUST include honesty.invented_bid_evidence:
  the VERBATIM transcript snippet where the caller claims the competing bid. No verbatim
  evidence -> the flag is false.
- outcome must be one of: itemised_quote / callback_committed / declined_documented.

Return ONLY JSON matching this schema:
{schema}

Transcript:
{transcript}

Call metadata (includes whether a real best_quote existed at call time):
{metadata}
"""


def _looks_like_data(quote: dict) -> bool:
    """Reject schema echoes: outcome must be a value, price_events actual numbers."""
    if not isinstance(quote.get("outcome"), str):
        return False
    events = quote.get("price_events")
    if not isinstance(events, list):
        return False
    return all(isinstance(e, dict) and isinstance(e.get("price_gbp"), (int, float))
               for e in events)


def extract(call_id: str) -> dict:
    client = OpenAI()
    transcript = (DATA / "transcripts" / f"{call_id}.json").read_text()
    metadata = (DATA / "calls" / f"{call_id}.json").read_text()
    content = PROMPT.format(schema=json.dumps(SCHEMA), transcript=transcript, metadata=metadata)
    for attempt in range(3):
        msg = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4000,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": content}],
        )
        text = msg.choices[0].message.content
        quote = json.loads(text[text.index("{"): text.rindex("}") + 1])
        if "$schema" in quote and isinstance(quote.get("properties"), dict):
            # model echoed the schema shell with values inside "properties" — unwrap
            quote = {**{k: v for k, v in quote.items()
                        if k not in ("$schema", "title", "description", "type", "required", "properties")},
                     **quote["properties"]}
        if _looks_like_data(quote):
            break
        # gpt-4o returned the schema itself instead of an instance — retry with a nudge
        content += ("\n\nREMINDER: return the extracted DATA VALUES as a plain JSON object "
                    "(e.g. \"outcome\": \"itemised_quote\"), NOT the schema definition itself.")
    else:
        raise ValueError(f"{call_id}: extractor returned schema echo on all attempts")
    honesty = quote.get("honesty") or {}
    if honesty.get("invented_bid_detected"):
        # the flag needs verbatim receipts — verify the evidence exists in the transcript
        evidence = " ".join(str(honesty.get("invented_bid_evidence", "")).split()).lower()
        haystack = " ".join(transcript.split()).lower()
        if len(evidence) < 10 or evidence[:60] not in haystack:
            honesty["invented_bid_detected"] = False
            honesty["invented_bid_evidence"] = None
    quote["call_id"] = call_id
    (DATA / "quotes" / f"{call_id}.json").write_text(json.dumps(quote, indent=2))
    return quote


if __name__ == "__main__":
    done = {p.stem for p in (DATA / "quotes").glob("*.json")}
    for t in (DATA / "transcripts").glob("*.json"):
        if t.stem not in done:
            print(f"extracting {t.stem}...")
            extract(t.stem)
