"""
Camada de abstracao de LLM com fallback offline deterministico.

Se OPENAI_API_KEY estiver presente, usa o modelo para enriquecer a
interpretacao das regras e as recomendacoes. Caso contrario, opera em
modo offline deterministico (sem internet, sem custo), garantindo que a
demo funcione ao vivo em qualquer ambiente.
"""
from __future__ import annotations

from config import settings


class LLMClient:
    def __init__(self) -> None:
        self.enabled = settings.USE_LLM
        self._client = None
        if self.enabled:
            try:
                from openai import OpenAI  # import tardio e opcional
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception:
                # Qualquer falha de import/credencial cai para offline.
                self.enabled = False

    @property
    def mode(self) -> str:
        return "llm" if self.enabled else "offline"

    def summarize_rule(self, descricao: str) -> str:
        """Resume/normaliza a descricao de uma regra de negocio."""
        if not self.enabled:
            return descricao.strip()
        try:
            resp = self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Resuma a regra de negocio em uma frase objetiva, em portugues."},
                    {"role": "user", "content": descricao},
                ],
                temperature=0,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return descricao.strip()

    def recommend(self, contexto: str) -> list[str]:
        """Gera recomendacoes de melhoria a partir das falhas."""
        if not self.enabled:
            return []
        try:
            resp = self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Gere recomendacoes tecnicas de melhoria, uma por linha, em portugues."},
                    {"role": "user", "content": contexto},
                ],
                temperature=0.2,
            )
            texto = resp.choices[0].message.content.strip()
            return [l.strip("-• ").strip() for l in texto.splitlines() if l.strip()]
        except Exception:
            return []
