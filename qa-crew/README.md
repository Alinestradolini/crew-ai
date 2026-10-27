# QA Crew — Testes Autônomos de API com Agentes de IA

Crew de agentes de inteligência artificial que interpreta documentação (OpenAPI/Swagger)
e regras de negócio em linguagem natural, gera e executa testes automatizados de APIs de
forma autônoma, identifica falhas e não conformidades e gera um **laudo técnico** com
indicadores de qualidade, evidências e recomendações — garantindo rastreabilidade entre
regras de negócio e resultados.

## Visão geral

```
┌─────────────────────────────────────────────────────────────────┐
│                           QA CREW                                 │
│                                                                   │
│  Doc (OpenAPI)  +  Regras de negócio (NL)                         │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │ 1. Analyst   │──▶│ 2. Designer  │──▶│ 3. Executor  │          │
│  │ interpreta   │   │ gera casos   │   │ roda testes  │          │
│  │ doc+regras   │   │ de teste     │   │ na API       │          │
│  └──────────────┘   └──────────────┘   └──────┬───────┘          │
│                                               │                   │
│                     ┌──────────────┐   ┌──────▼───────┐          │
│                     │ 5. Reporter  │◀──│ 4. Auditor   │          │
│                     │ laudo HTML   │   │ não conform. │          │
│                     │ +JSON+indic. │   │ rastreab.    │          │
│                     └──────────────┘   └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

A Crew tem 5 agentes especializados que operam em pipeline:

1. **Analyst** — interpreta a documentação OpenAPI e as regras de negócio em linguagem natural.
2. **Designer** — projeta os casos de teste derivados de cada regra (positivos e negativos).
3. **Executor** — executa os testes HTTP contra a API alvo e coleta evidências.
4. **Auditor** — avalia conformidade, classifica falhas e mantém a rastreabilidade regra→teste→resultado.
5. **Reporter** — gera o laudo técnico (HTML + JSON) com indicadores de qualidade e recomendações.

## Dois modos de LLM

- **Modo LLM** (se houver `OPENAI_API_KEY`): os agentes usam o modelo para interpretar regras ambíguas.
- **Modo offline/determinístico** (padrão): os agentes usam um motor de regras interno.
  Garante demo ao vivo 100% funcional sem internet nem custo.

O sistema detecta automaticamente qual modo usar.

## Como rodar (demo ao vivo)

```bash
cd qa-crew
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# 1) Sobe a API alvo mock (terminal 1)
python -m uvicorn target_api.app:app --port 8000

# 2) Roda a Crew contra a API (terminal 2)
python -m qa_crew.main --base-url http://localhost:8000

# 3) Abre o laudo gerado
# reports/laudo.html
```

Ou use o atalho único (sobe API, roda crew e abre laudo):

```bash
python run_demo.py
```

### Demo de detecção de falhas (impacto na apresentação)

Para mostrar ao vivo que a Crew identifica não conformidades, rode a API em
modo defeituoso (viola RN02 e RN06 de propósito):

```bash
python run_demo_falhas.py
```

O laudo mostrará taxa de sucesso em 80%, duas não conformidades classificadas
por severidade (alta e média), com evidências e recomendações.

## Estrutura

```
qa-crew/
├── README.md
├── requirements.txt
├── run_demo.py                  # Orquestra a demo completa
├── config/
│   ├── business_rules.yaml      # Regras de negócio em linguagem natural
│   └── settings.py              # Configurações
├── target_api/                  # API ALVO mock (sistema sob teste)
│   ├── app.py                   # FastAPI: usuários, pedidos, auth
│   └── openapi_sample.json      # Documentação exportada
├── qa_crew/                     # A CREW de agentes
│   ├── main.py                  # Ponto de entrada / orquestrador
│   ├── crew.py                  # Montagem da crew e pipeline
│   ├── llm.py                   # Camada LLM com fallback offline
│   ├── models.py                # Modelos de dados (dataclasses)
│   ├── agents/
│   │   ├── analyst.py           # Agente 1
│   │   ├── designer.py          # Agente 2
│   │   ├── executor.py          # Agente 3
│   │   ├── auditor.py           # Agente 4
│   │   └── reporter.py          # Agente 5
│   └── report/
│       └── template.py          # Geração do laudo HTML
├── tests/
│   └── test_pipeline.py         # Testes do próprio sistema
└── reports/                     # Saída: laudo.html + laudo.json
```

## Indicadores do laudo

- Total de regras, cobertura de regras testadas
- Total de casos, aprovados, reprovados, taxa de sucesso
- Não conformidades por severidade (crítica/alta/média/baixa)
- Tempo médio de resposta por endpoint
- Matriz de rastreabilidade regra → caso → resultado → evidência
- Recomendações de melhoria priorizadas

## Mapeamento aos critérios de avaliação

**1. Protótipo Funcional (MVP) — 30 pts**
- Funcionalidade principal implementada e utilizável: pipeline de 5 agentes que interpreta regras, gera, executa e audita testes, e emite laudo. ✔
- Demonstração funcional ao vivo com dados mock: `run_demo.py` e `run_demo_falhas.py` sobem a API mock e rodam a Crew de ponta a ponta. ✔
- Fluxo principal navegável: console mostra cada etapa; laudo HTML interativo com drill-down de evidências. ✔

**2. Resolução do Problema — 20 pts**
- Resolve o problema: valida comportamento dos endpoints conforme requisitos, identifica falhas e não conformidades, gera laudo com indicadores, evidências e recomendações, com rastreabilidade regra→resultado. ✔
- Aplicabilidade real: regras de negócio ficam em YAML legível por negócio; integra em CI (código de saída != 0 em falhas críticas/altas); funciona contra qualquer API HTTP via `--base-url`. ✔

**3. Inovação — 20 pts**
- Abordagem por Crew de agentes especializados em pipeline, orientada por regras de negócio em linguagem natural (não por scripts de teste manuais). ✔
- Modo LLM com fallback offline determinístico: criativo e pragmático — garante demo sem dependência de internet/custo, e enriquece com IA quando há chave. ✔

**4. Apresentação Final — 10 pts**
- Pitch com linha lógica: problema → Crew de agentes → demo sucesso → demo falhas → laudo. Roteiro sugerido abaixo.

**5. Execução e Completude — 10 pts**
- Estrutura mínima completa: API alvo (cadastro/login/pedidos), fluxo de testes, laudo (tela HTML) e saída JSON. ✔
- Partes conectadas de forma coesa: Analyst → Designer → Executor → Auditor → Reporter, com modelos de dados compartilhados. ✔

## Roteiro de pitch (sugestão, ~5 min)

1. Problema: testar APIs contra regras de negócio é manual, lento e sem rastreabilidade.
2. Solução: uma Crew de 5 agentes de IA que lê a documentação e as regras e testa sozinha.
3. Demo 1 (`run_demo.py`): a Crew valida a API — 100% conforme, laudo com indicadores.
4. Demo 2 (`run_demo_falhas.py`): injetamos bugs — a Crew detecta, classifica severidade e recomenda correções.
5. Fechamento: rastreabilidade regra→caso→resultado→evidência, pronto para CI.

## Testes do próprio sistema

```bash
python -m pytest tests/ -v
```
