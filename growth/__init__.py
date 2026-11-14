"""
Pipeleap Growth Loop.

MEASURE -> LEARN -> PLAN -> ACT -> REPORT, against the site that is actually live.

Design rules (each one exists because the previous system broke it):
  1. Outcomes only. Nothing the loop does to itself (pages generated, actions
     queued) counts toward any score. Only search and enquiry data does.
  2. Unknown is a valid answer. A data source that is unreachable is reported
     as unreachable, never back-filled with estimates.
  3. Every change is an experiment with a baseline, a hypothesis and a verdict.
  4. State lives in the repository (growth_state/), not in a CI cache.
  5. The site checkout is the source of truth for what Pipeleap says about
     itself. Positioning is read from it on every run, never hardcoded.
  6. No content ships without passing the quality gate, and nothing is
     generated from templates.
"""

__version__ = "2.0.0"
