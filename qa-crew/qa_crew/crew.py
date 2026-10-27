"""
Orquestrador da QA Crew.

Monta os 5 agentes e executa o pipeline sequencial:
  Analyst -> Designer -> Executor -> Auditor -> Reporter
Emite logs de progresso no console (rich) e devolve o QAReport.
"""
from __future__ import annotations

import json

from rich.console import Console

from config import settings
from qa_crew.agents.analyst import Analyst
from qa_crew.agents.auditor import Auditor
from qa_crew.agents.designer import Designer
from qa_crew.agents.executor import Executor
from qa_crew.agents.reporter import Reporter
from qa_crew.llm import LLMClient
from qa_crew.models import QAReport
from qa_crew.report.template import render_html

console = Console()


class QACrew:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.llm = LLMClient()
        self.analyst = Analyst(self.llm)
        self.designer = Designer()
        self.executor = Executor(base_url)
        self.auditor = Auditor()
        self.reporter = Reporter(self.llm)

    def run(self) -> QAReport:
        console.rule("[bold cyan]QA CREW - Testes autonomos de API")
        console.print(f"Modo LLM: [bold]{self.llm.mode}[/bold]  |  Alvo: {self.base_url}\n")

        console.print("[1/5] [bold]Analyst[/bold] interpretando documentacao e regras...")
        rules, meta = self.analyst.run(settings.BUSINESS_RULES_PATH, settings.OPENAPI_PATH)
        console.print(f"      {len(rules)} regras interpretadas "
                      f"({meta['regras_com_doc']} com doc OpenAPI).")

        console.print("[2/5] [bold]Designer[/bold] projetando casos de teste...")
        cases = self.designer.run(rules)
        console.print(f"      {len(cases)} casos de teste gerados.")

        console.print("[3/5] [bold]Executor[/bold] executando testes na API...")
        evidencias = self.executor.run(cases)
        console.print(f"      {len(evidencias)} execucoes coletadas.")

        console.print("[4/5] [bold]Auditor[/bold] auditando conformidade...")
        results = self.auditor.run(cases, evidencias)
        reprovados = sum(1 for r in results if not r.passou)
        console.print(f"      {reprovados} nao conformidades identificadas.")

        console.print("[5/5] [bold]Reporter[/bold] gerando laudo tecnico...")
        report = self.reporter.run(rules, results, self.base_url, meta)
        console.print("      laudo consolidado.\n")

        self._print_resumo(report)
        return report

    def save(self, report: QAReport) -> tuple[str, str]:
        settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        html_path = settings.REPORTS_DIR / "laudo.html"
        json_path = settings.REPORTS_DIR / "laudo.json"

        html_path.write_text(render_html(report), encoding="utf-8")
        json_path.write_text(self._to_json(report), encoding="utf-8")
        console.print(f"[green]Laudo HTML:[/green] {html_path}")
        console.print(f"[green]Laudo JSON:[/green] {json_path}")
        return str(html_path), str(json_path)

    def _print_resumo(self, report: QAReport) -> None:
        i = report.indicadores
        console.rule("[bold]Resumo")
        console.print(f"Taxa de sucesso: [bold]{i['taxa_sucesso_pct']}%[/bold]  |  "
                      f"Cobertura de regras: [bold]{i['cobertura_regras_pct']}%[/bold]  |  "
                      f"Casos: {i['casos_aprovados']}/{i['casos_total']}")
        nc = i["nao_conformidades"]
        console.print(f"Nao conformidades -> critica:{nc['critica']} alta:{nc['alta']} "
                      f"media:{nc['media']} baixa:{nc['baixa']}\n")

    @staticmethod
    def _to_json(report: QAReport) -> str:
        payload = {
            "base_url": report.base_url,
            "modo_llm": report.modo_llm,
            "indicadores": report.indicadores,
            "recomendacoes": report.recomendacoes,
            "rastreabilidade": [
                {
                    "regra": r.case.rule_id,
                    "caso": r.case.id,
                    "nome": r.case.nome,
                    "endpoint": f"{r.case.metodo} {r.case.endpoint}",
                    "passou": r.passou,
                    "motivo": r.motivo,
                    "severidade": r.severidade,
                    "evidencia": None if not r.evidencia else {
                        "status": r.evidencia.response_status,
                        "tempo_ms": r.evidencia.elapsed_ms,
                        "requisicao": r.evidencia.request_body,
                        "resposta": r.evidencia.response_body,
                    },
                }
                for r in report.results
            ],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
