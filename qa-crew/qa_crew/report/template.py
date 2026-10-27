"""Geracao do laudo tecnico em HTML a partir do QAReport."""
from __future__ import annotations

import json
from datetime import datetime

from jinja2 import Template

from qa_crew.models import QAReport

_HTML = Template(
    """<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laudo Tecnico - QA Crew</title>
<style>
  :root{--ok:#1f9d55;--bad:#e3342f;--crit:#b91c1c;--alta:#ea580c;--media:#ca8a04;--baixa:#6b7280;}
  *{box-sizing:border-box} body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f5f6f8;color:#1f2933}
  header{background:#0f172a;color:#fff;padding:28px 32px}
  header h1{margin:0;font-size:22px} header p{margin:4px 0 0;color:#94a3b8;font-size:13px}
  .wrap{max-width:1080px;margin:0 auto;padding:24px 32px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:16px 0}
  .card{background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
  .card .v{font-size:26px;font-weight:700} .card .l{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.04em}
  .bar{height:10px;border-radius:6px;background:#e2e8f0;overflow:hidden;margin-top:6px}
  .bar>span{display:block;height:100%;background:var(--ok)}
  h2{margin:28px 0 10px;font-size:17px}
  table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}
  th,td{padding:10px 12px;text-align:left;font-size:13px;border-bottom:1px solid #eef2f7;vertical-align:top}
  th{background:#f1f5f9;font-size:12px;text-transform:uppercase;color:#475569}
  .pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:700;color:#fff}
  .pass{background:var(--ok)} .fail{background:var(--bad)}
  .sev-critica{background:var(--crit)} .sev-alta{background:var(--alta)}
  .sev-media{background:var(--media)} .sev-baixa{background:var(--baixa)}
  details{background:#fff;border-radius:8px;margin:6px 0;padding:8px 12px;box-shadow:0 1px 2px rgba(0,0,0,.06)}
  summary{cursor:pointer;font-size:13px;font-weight:600}
  pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto;font-size:12px}
  .rec{background:#fff;border-left:4px solid #0ea5e9;padding:10px 14px;margin:6px 0;border-radius:4px;font-size:13px}
  .mode{display:inline-block;background:#334155;color:#fff;padding:2px 10px;border-radius:999px;font-size:11px}
  footer{color:#94a3b8;font-size:12px;text-align:center;padding:24px}
</style>
</head>
<body>
<header>
  <h1>Laudo Tecnico de Testes Autonomos de API</h1>
  <p>Gerado por QA Crew em {{ data }} &middot; Alvo: {{ r.base_url }} &middot;
     <span class="mode">modo {{ r.modo_llm }}</span></p>
</header>
<div class="wrap">

  <div class="cards">
    <div class="card"><div class="v">{{ i.taxa_sucesso_pct }}%</div><div class="l">Taxa de sucesso</div>
      <div class="bar"><span style="width:{{ i.taxa_sucesso_pct }}%"></span></div></div>
    <div class="card"><div class="v">{{ i.cobertura_regras_pct }}%</div><div class="l">Cobertura de regras</div></div>
    <div class="card"><div class="v">{{ i.casos_aprovados }}/{{ i.casos_total }}</div><div class="l">Casos aprovados</div></div>
    <div class="card"><div class="v">{{ i.casos_reprovados }}</div><div class="l">Nao conformidades</div></div>
    <div class="card"><div class="v">{{ i.tempo_medio_ms }} ms</div><div class="l">Tempo medio</div></div>
  </div>

  <h2>Nao conformidades por severidade</h2>
  <div class="cards">
    <div class="card"><div class="v" style="color:var(--crit)">{{ i.nao_conformidades.critica }}</div><div class="l">Critica</div></div>
    <div class="card"><div class="v" style="color:var(--alta)">{{ i.nao_conformidades.alta }}</div><div class="l">Alta</div></div>
    <div class="card"><div class="v" style="color:var(--media)">{{ i.nao_conformidades.media }}</div><div class="l">Media</div></div>
    <div class="card"><div class="v" style="color:var(--baixa)">{{ i.nao_conformidades.baixa }}</div><div class="l">Baixa</div></div>
  </div>

  <h2>Matriz de rastreabilidade (regra &rarr; caso &rarr; resultado)</h2>
  <table>
    <thead><tr><th>Regra</th><th>Caso de teste</th><th>Endpoint</th><th>Status HTTP</th><th>Resultado</th><th>Severidade</th></tr></thead>
    <tbody>
    {% for res in r.results %}
      <tr>
        <td><strong>{{ res.case.rule_id }}</strong></td>
        <td>{{ res.case.nome }}</td>
        <td>{{ res.case.metodo }} {{ res.case.endpoint }}</td>
        <td>{{ res.evidencia.response_status if res.evidencia else '-' }}</td>
        <td>{% if res.passou %}<span class="pill pass">APROVADO</span>{% else %}<span class="pill fail">REPROVADO</span>{% endif %}</td>
        <td>{% if res.severidade %}<span class="pill sev-{{ res.severidade }}">{{ res.severidade|upper }}</span>{% else %}-{% endif %}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>

  <h2>Evidencias dos testes</h2>
  {% for res in r.results %}
  <details>
    <summary>{{ res.case.id }} &middot; {{ res.case.nome }} &middot;
      {% if res.passou %}APROVADO{% else %}REPROVADO - {{ res.motivo }}{% endif %}</summary>
    {% if res.evidencia %}
    <pre>{{ render_evidence(res) }}</pre>
    {% else %}<p>Sem evidencia.</p>{% endif %}
  </details>
  {% endfor %}

  <h2>Recomendacoes de melhoria</h2>
  {% for rec in r.recomendacoes %}
    <div class="rec">{{ rec }}</div>
  {% endfor %}

</div>
<footer>QA Crew &middot; Testes autonomos de API orientados por regras de negocio</footer>
</body>
</html>"""
)


def _render_evidence(res) -> str:
    ev = res.evidencia
    data = {
        "requisicao": {
            "metodo": ev.request_method,
            "url": ev.request_url,
            "corpo": ev.request_body,
        },
        "resposta": {
            "status": ev.response_status,
            "tempo_ms": ev.elapsed_ms,
            "corpo": ev.response_body,
        },
        "avaliacao": {"passou": res.passou, "motivo": res.motivo,
                      "severidade": res.severidade},
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def render_html(report: QAReport) -> str:
    return _HTML.render(
        r=report,
        i=report.indicadores,
        data=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        render_evidence=_render_evidence,
    )
