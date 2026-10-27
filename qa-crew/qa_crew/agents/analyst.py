"""
Agente 1 - Analyst.

Interpreta a documentacao (OpenAPI) e as regras de negocio em linguagem
natural, consolidando-as em objetos BusinessRule estruturados. Usa o LLM
para normalizar descricoes quando disponivel.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from qa_crew.llm import LLMClient
from qa_crew.models import BusinessRule


class Analyst:
    nome = "Analyst"
    papel = "Interpreta documentacao e regras de negocio"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, rules_path: Path, openapi_path: Path) -> tuple[list[BusinessRule], dict]:
        openapi = self._load_openapi(openapi_path)
        rules = self._load_rules(rules_path)
        endpoints_doc = set(openapi.get("paths", {}).keys())

        parsed: list[BusinessRule] = []
        for r in rules:
            descricao = self.llm.summarize_rule(r.get("descricao", ""))
            parsed.append(
                BusinessRule(
                    id=r["id"],
                    titulo=r.get("titulo", r["id"]),
                    descricao=descricao,
                    endpoint=r["endpoint"],
                    metodo=r["metodo"].upper(),
                    criterios=r.get("criterios", []),
                )
            )

        # Cobertura documental: regras cujo endpoint consta na OpenAPI
        cobertos = [r for r in parsed if self._match_doc(r.endpoint, endpoints_doc)]
        meta = {
            "endpoints_documentados": sorted(endpoints_doc),
            "regras_total": len(parsed),
            "regras_com_doc": len(cobertos),
        }
        return parsed, meta

    @staticmethod
    def _match_doc(endpoint: str, docs: set[str]) -> bool:
        # Compara ignorando parametros de path concretos
        base = endpoint.split("{")[0].rstrip("/")
        for d in docs:
            if d.split("{")[0].rstrip("/") == base:
                return True
        return False

    @staticmethod
    def _load_openapi(path: Path) -> dict:
        if not path.exists():
            return {"paths": {}}
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_rules(path: Path) -> list[dict]:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("rules", [])
