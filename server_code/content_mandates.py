"""Specialist programs (added 2026-11-18): Board Mandates (M&A, activist investors, AI governance) and Hiring Judgment.

The modules live in their own files, each researched and source-checked separately:
  content_board_ma.py   M&A deal thesis, M&A integration, activist investors, their cases and the Board Mandates capstone
  content_board_ai.py   AI governance: board oversight and deploying AI in practice, and their cases
  content_hiring.py     Hiring Judgment: the method + product, marketing, operations and project leaders, cases, capstone
Same module and case formats as content_roles_a.py and content_cases.py. Curriculum.py adds TRACKS; content_cases.py
appends CASES to the Casebook.
"""
from . import content_board_ai, content_board_ma, content_hiring

BOARD = {
    "id": "board", "code": "BMD", "order": 8, "title": "Board Mandates", "role": "Directors and the C-suite",
    "credential": "Certificate in Board Mandates", "photo": "ph-board-table",
    "blurb": "The decisions boards get judged on: acquisitions, activist investors and the governance of AI.",
    "outcomes": ["Test an acquisition on value, price discipline and integration, not size",
                 "Prepare for and respond to an activist campaign",
                 "Oversee AI: who owns the risk, which rules apply, and what the company may claim"],
}

TRACKS = [
    {"track": BOARD, "modules": content_board_ma.MODULES + content_board_ai.MODULES, "capstone": content_board_ma.CAPSTONE},
    {"track": content_hiring.TRACK, "modules": content_hiring.MODULES, "capstone": content_hiring.CAPSTONE},
]

CASES = content_board_ma.CASES + content_board_ai.CASES + content_hiring.CASES
