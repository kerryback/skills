"""coauthor: reusable multi-agent machinery for empirical research papers.

Modules:
  config    — locate the project, load the debate-voice roster + charters
  debate    — stateless OpenRouter voice call (charter + brief -> JSON), logged
  logging_  — canonical JSONL sink with secret redaction
  render    — JSONL -> readable per-round transcripts (Markdown + HTML)
"""
__version__ = "0.1.0"
