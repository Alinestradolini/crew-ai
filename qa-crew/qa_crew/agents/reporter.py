"""
Agente 5 - Reporter.

Consolida os resultados em um laudo tecnico: calcula indicadores de
qualidade, prioriza recomendacoes de melhoria e monta o objeto QAReport.
"""
from __future__ import annotations

from statistics import mean

from config import settings
from qa_crew.llm import LLMClient
from qa_crew.models import BusinessRule, QAReport, TestResult


class Reporter:
    nome = "Reporter"
    papel = "Gera o laudo tecnico com indicadores e recomendacoes"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, rules: list[BusinessRule], results: list[TestResult],
            base_url: str, meta: dict) -> QAReport:
        total = len(results)
        aprovados = sum(1 for r in results if r.passou)
        reprovados = total - aprovados
        taxa = round((aprovados / total) * 100, 1) if total else 0.0

        regras_testadas = {r.case.rule_id for r in results}
        cobertura = round((len(regras_testadas) / len(rules)) * 100, 1) if rules else 0.0

        severidades = {
            settings.SEVERITY_CRITICAL: 0,
            settings.SEVERITY_HIGH: 0,
            settings.SEVERITY_MEDIUM: 0,
            settings.SEVERITY_LOW: 0,
        }
        for r in results:
            if not r.passou and r.severidade in severidades:
                severidades[r.severidade] += 1

        tempos = [r.evidencia.elapsed_ms for r in results if r.evidencia]
        tempo_medio = round(mean(tempos), 2) if tempos else 0.0

        indicadores = {
            "regras_total": len(rules),
            "regras_testadas": len(regras_testadas),
            "cobertura_regras_pct": cobertura,
            "casos_total": total,
            "casos_aprovados": aprovados,
            "casos_reprovados": reprovados,
            "taxa_sucesso_pct": taxa,
            "nao_conformidades": severidades,
            "tempo_medio_ms": tempo_medio,
            "endpoints_documentados": meta.get("endpoints_documentados", []),
        }

        recomendacoes = self._recomendacoes(results)

        return QAReport(
            rules=rules,
            results=results,
            indicadores=indicadores,
            recomendacoes=recomendacoes,
            modo_llm=self.llm.mode,
            base_url=base_url,
        )

    def _recomendacoes(self, results: list[TestResult]) -> list[str]:
        falhas = [r for r in results if not r.passou]
        if not falhas:
            return ["Todos os casos passaram. Manter a suite em pipeline de CI para regressao."]

        base: list[str] = []
        for r in falhas:
            base.append(
                f"[{r.case.rule_id}] {r.case.nome}: {r.motivo}. "
                f"Revisar o endpoint {r.case.metodo} {r.case.endpoint}."
            )

        # Enriquecimento opcional via LLM
        contexto = "\n".join(base)
        extra = self.llm.recommend(contexto)
        if extra:
            base.append("--- Sugestoes adicionais (LLM) ---")
            base.extend(extra)
        return base
