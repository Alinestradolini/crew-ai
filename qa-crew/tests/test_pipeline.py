"""
Testes do proprio sistema QA Crew.

Sobe a API alvo real em um servidor uvicorn em background (thread) e executa
o pipeline completo contra ela, validando interpretacao, geracao de casos,
execucao, auditoria, rastreabilidade e indicadores.
"""
from __future__ import annotations

import socket
import threading
import time

import httpx
import pytest
import uvicorn

from config import settings
from qa_crew.agents.analyst import Analyst
from qa_crew.agents.auditor import Auditor
from qa_crew.agents.designer import Designer
from qa_crew.agents.executor import Executor
from qa_crew.agents.reporter import Reporter
from qa_crew.llm import LLMClient
from target_api.app import app


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def live_server():
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    # aguarda ficar saudavel
    for _ in range(40):
        try:
            if httpx.get(f"{base_url}/health", timeout=1.0).status_code == 200:
                break
        except httpx.RequestError:
            time.sleep(0.25)
    else:
        pytest.fail("API alvo nao subiu a tempo")

    yield base_url
    server.should_exit = True
    thread.join(timeout=5)


def _run_pipeline(base_url):
    llm = LLMClient()
    rules, meta = Analyst(llm).run(settings.BUSINESS_RULES_PATH, settings.OPENAPI_PATH)
    cases = Designer().run(rules)
    evidencias = Executor(base_url).run(cases)
    results = Auditor().run(cases, evidencias)
    report = Reporter(llm).run(rules, results, base_url, meta)
    return rules, cases, results, report


def test_analyst_le_todas_as_regras():
    rules, meta = Analyst(LLMClient()).run(settings.BUSINESS_RULES_PATH, settings.OPENAPI_PATH)
    assert len(rules) == 7
    assert meta["regras_total"] == 7


def test_designer_gera_casos_para_cada_criterio():
    rules, _ = Analyst(LLMClient()).run(settings.BUSINESS_RULES_PATH, settings.OPENAPI_PATH)
    cases = Designer().run(rules)
    total_criterios = sum(len(r.criterios) for r in rules)
    assert len(cases) == total_criterios
    assert all(c.rule_id for c in cases)


def test_pipeline_completo_todos_conformes(live_server):
    _, _, results, report = _run_pipeline(live_server)
    reprovados = [r for r in results if not r.passou]
    assert not reprovados, [f"{r.case.id}: {r.motivo}" for r in reprovados]
    assert report.indicadores["taxa_sucesso_pct"] == 100.0
    assert report.indicadores["cobertura_regras_pct"] == 100.0


def test_rastreabilidade_regra_para_caso(live_server):
    rules, _, results, _ = _run_pipeline(live_server)
    rule_ids = {r.id for r in rules}
    for res in results:
        assert res.case.rule_id in rule_ids
        assert res.evidencia is not None


def test_indicadores_consistentes(live_server):
    _, cases, results, report = _run_pipeline(live_server)
    i = report.indicadores
    assert i["casos_total"] == len(cases)
    assert i["casos_aprovados"] + i["casos_reprovados"] == i["casos_total"]
    assert 0 <= i["taxa_sucesso_pct"] <= 100
