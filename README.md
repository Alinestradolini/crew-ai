# QA Crew — Testes Autônomos de API com Agentes de IA

Crew de agentes de inteligência artificial que interpreta documentação (OpenAPI/Swagger)
e regras de negócio em linguagem natural, gera e executa testes automatizados de APIs de
forma autônoma, identifica falhas e não conformidades e gera um **laudo técnico** com
indicadores de qualidade, evidências e recomendações — garantindo rastreabilidade entre
regras de negócio e resultados.

## Visão geral

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

# 3) Abre o laudo gerado em reports/laudo.html
```

Ou use o atalho único (sobe API, roda crew e abre laudo):

```bash
python run_demo.py
```

Para demonstrar a detecção de não conformidades (API em modo defeituoso):

```bash
python run_demo_falhas.py
```

## Documentação completa

A documentação detalhada, estrutura do projeto, indicadores do laudo e roteiro de pitch
estão em [`qa-crew/README.md`](qa-crew/README.md).
