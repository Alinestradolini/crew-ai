"""
Agente 3 - Executor.

Executa os casos de teste contra a API alvo via HTTP, coletando evidencias
(request, response, status, tempo). Gerencia autenticacao (login automatico)
e dependencias entre casos (ex.: um caso pode depender de outro ter rodado).
"""
from __future__ import annotations

import time
from typing import Optional

import httpx

from qa_crew.models import Evidence, TestCase


class Executor:
    nome = "Executor"
    papel = "Executa os testes na API e coleta evidencias"

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token: Optional[str] = None
        # contexto de dados produzidos por casos anteriores (p/ dependencias)
        self.contexto: dict[str, dict] = {}

    def ensure_login(self, client: httpx.Client) -> Optional[str]:
        """Garante um token valido, fazendo login com o usuario semente."""
        if self._token:
            return self._token
        # usuario semente criado por RN01
        resp = client.post(
            f"{self.base_url}/login",
            json={"email": "ana@exemplo.com", "password": "senha123"},
        )
        if resp.status_code == 200:
            self._token = resp.json().get("access_token")
        return self._token

    def run(self, cases: list[TestCase]) -> dict[str, Evidence]:
        evidencias: dict[str, Evidence] = {}
        with httpx.Client(timeout=10.0) as client:
            for case in cases:
                headers = {}
                if case.requer_login and not case.sem_auth:
                    token = self.ensure_login(client)
                    if token:
                        headers["Authorization"] = f"Bearer {token}"

                url = f"{self.base_url}{self._resolve_path(case)}"
                started = time.perf_counter()
                try:
                    resp = self._dispatch(client, case, url, headers)
                    elapsed = (time.perf_counter() - started) * 1000
                    body = self._safe_json(resp)
                    evidencias[case.id] = Evidence(
                        request_method=case.metodo,
                        request_url=url,
                        request_body=case.payload,
                        response_status=resp.status_code,
                        response_body=body,
                        elapsed_ms=round(elapsed, 2),
                    )
                    # guarda contexto (ex.: id do pedido criado)
                    if isinstance(body, dict):
                        self.contexto[case.id] = body
                except httpx.RequestError as exc:
                    elapsed = (time.perf_counter() - started) * 1000
                    evidencias[case.id] = Evidence(
                        request_method=case.metodo,
                        request_url=url,
                        request_body=case.payload,
                        response_status=0,
                        response_body={"erro_conexao": str(exc)},
                        elapsed_ms=round(elapsed, 2),
                    )
        return evidencias

    def _resolve_path(self, case: TestCase) -> str:
        path = case.endpoint
        if case.path_param:
            for k, v in case.path_param.items():
                path = path.replace("{" + k + "}", str(v))
        return path

    @staticmethod
    def _dispatch(client: httpx.Client, case: TestCase, url: str, headers: dict):
        method = case.metodo.upper()
        if method == "GET":
            return client.get(url, headers=headers)
        if method == "POST":
            return client.post(url, json=case.payload or {}, headers=headers)
        if method == "PUT":
            return client.put(url, json=case.payload or {}, headers=headers)
        if method == "DELETE":
            return client.delete(url, headers=headers)
        raise ValueError(f"Metodo nao suportado: {method}")

    @staticmethod
    def _safe_json(resp: httpx.Response):
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}
