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
- outcome must be one of: itemised_quote / callback_committed / declined_documented.

Return ONLY JSON matching this schema:
{schema}

Transcript:
{transcript}

Call metadata (includes whether a real best_quote existed at call time):
{metadata}
"""


def extract(call_id: str) -> dict:
    client = OpenAI()
    transcript = (DATA / "transcripts" / f"{call_id}.json").read_text()
    metadata = (DATA / "calls" / f"{call_id}.json").read_text()
    msg = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT.format(
            schema=json.dumps(SCHEMA), transcript=transcript, metadata=metadata)}],
    )
    text = msg.choices[0].message.content
    quote = json.loads(text[text.index("{"): text.rindex("}") + 1])
    quote["call_id"] = call_id
    (DATA / "quotes" / f"{call_id}.json").write_text(json.dumps(quote, indent=2))
    return quote


if __name__ == "__main__":
    done = {p.stem for p in (DATA / "quotes").glob("*.json")}
    for t in (DATA / "transcripts").glob("*.json"):
        if t.stem not in done:
            print(f"extracting {t.stem}...")
            extract(t.stem)
