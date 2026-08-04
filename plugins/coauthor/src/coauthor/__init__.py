"""coauthor: reusable multi-agent machinery for empirical research papers.

Modules:
  config    — locate the project, load the debate-voice roster + charters
  debate    — stateless OpenRouter voice call (charter + brief -> JSON), logged
  logging_  — canonical JSONL sink with secret redaction
  runid     — the <user>-<date>-<time> stamp that names every log artifact
"""
__version__ = "0.4.0"
