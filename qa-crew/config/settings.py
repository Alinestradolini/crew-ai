"""Configuracoes centrais da QA Crew."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUSINESS_RULES_PATH = ROOT / "config" / "business_rules.yaml"
OPENAPI_PATH = ROOT / "target_api" / "openapi_sample.json"
REPORTS_DIR = ROOT / "reports"

DEFAULT_BASE_URL = os.getenv("TARGET_BASE_URL", "http://localhost:8000")

# LLM: usa OpenAI se a chave existir; senao, modo offline deterministico.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
USE_LLM = bool(OPENAI_API_KEY)

# Severidades de nao conformidade
SEVERITY_CRITICAL = "critica"
SEVERITY_HIGH = "alta"
SEVERITY_MEDIUM = "media"
SEVERITY_LOW = "baixa"
