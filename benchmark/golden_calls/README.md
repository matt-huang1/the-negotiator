# Golden calls

The frozen evidence set: the best end-to-end calls (transcripts, extracted
quotes, call metadata) plus the harness output computed from them.

Why frozen: (1) reproducible evidence — the harness runs over these files and
the numbers don't change; (2) regression set — after any prompt tweak, re-run
the same scenario and confirm the agent still moves price and passes the
honesty checks.

Contents: one call per persona (aggressive / evasive / honest), including one
with leverage-attributed price movement (£2,100 → £1,740). ElevenLabs resource
IDs in the transcripts are redacted; the dialogue and price evidence are
verbatim.
