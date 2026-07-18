"""Ranked comparison report — Streamlit.

Run: streamlit run report/app.py
"""
import json
from pathlib import Path

import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from benchmark.harness import scoreboard  # noqa: E402
from server.redflag import flags_for  # noqa: E402

DATA = Path("./data")

st.set_page_config(page_title="The Negotiator", layout="wide")
st.title("The Negotiator — ranked quotes")

quotes = [json.loads(p.read_text()) for p in sorted((DATA / "quotes").glob("*.json"))]
if not quotes:
    st.info("No quotes yet. Run calls, then `python -m server.quote_extractor`.")
    st.stop()

# ---- Harness scoreboard (the headline) ----
sb = scoreboard()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total price movement", f"£{sb['total_movement_gbp']}")
c2.metric("Attributed to leverage", f"£{sb['total_leverage_attributed_gbp']}")
c3.metric("Calls / styles", f"{sb['n_calls']} / {sb['n_personas']}")
c4.metric("Best single-call movement", f"{sb['best_single_movement_pct']}%")

# ---- Ranking: not just cheapest — binding + flags + terms ----
def rank_key(q):
    penalty = 200 * len(q.get("red_flags", [])) + (0 if q.get("binding") else 150)
    return (q.get("total_gbp") or 9e9) + penalty

ranked = sorted(quotes, key=rank_key)
st.subheader("Recommendation")
best = ranked[0]
st.success(
    f"**{best.get('company', best['call_id'])}** — £{best.get('total_gbp', '?')} "
    f"({'binding' if best.get('binding') else 'non-binding'}). "
    f"Ranked on price AND terms: red flags and non-binding quotes are penalised, "
    f"so the cheapest lowball does not automatically win."
)

for i, q in enumerate(ranked, 1):
    flags = flags_for(q.get("total_gbp") or 0, q.get("itemised_fees", []))
    with st.expander(
        f"#{i}  {q.get('company', q['call_id'])} — £{q.get('total_gbp', '?')} "
        f"[{q.get('persona_style')}] {'🚩' * len(flags)}"
    ):
        left, right = st.columns(2)
        with left:
            st.write("**Itemised fees**")
            st.table(q.get("itemised_fees", []))
            for f in flags:
                st.warning(f)
        with right:
            st.write("**Price journey (evidence)**")
            for e in q.get("price_events", []):
                st.write(f"- `t={e['t_seconds']:.0f}s` £{e['price_gbp']} — *{e['trigger']}*  \n"
                         f"  > {e.get('transcript_snippet', '')}")
            t = DATA / "transcripts" / f"{q['call_id']}.json"
            if t.exists():
                st.download_button("Full transcript", t.read_text(),
                                   file_name=t.name, key=f"dl-{q['call_id']}")
