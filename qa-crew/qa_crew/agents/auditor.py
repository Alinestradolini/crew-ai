"""
Agente 4 - Auditor.

Avalia cada evidencia contra o resultado esperado do caso de teste,
classifica nao conformidades por severidade e mantem a rastreabilidade
regra -> caso -> resultado -> evidencia.
"""
from __future__ import annotations

from config import settings
from qa_crew.models import Evidence, TestCase, TestResult


class Auditor:
    nome = "Auditor"
    papel = "Audita conformidade e classifica nao conformidades"

    def run(self, cases: list[TestCase], evidencias: dict[str, Evidence]) -> list[TestResult]:
        resultados: list[TestResult] = []
        for case in cases:
            ev = evidencias.get(case.id)
            if ev is None:
                resultados.append(
                    TestResult(case=case, passou=False,
                               motivo="Sem evidencia (nao executado)",
                               severidade=settings.SEVERITY_HIGH)
                )
                continue
            passou, motivo = self._avaliar(case, ev)
            severidade = None if passou else self._severidade(case, ev)
            resultados.append(
                TestResult(case=case, passou=passou, motivo=motivo,
                           severidade=severidade, evidencia=ev)
            )
        return resultados

    def _avaliar(self, case: TestCase, ev: Evidence) -> tuple[bool, str]:
        if ev.response_status == 0:
            return False, f"Falha de conexao com a API: {ev.response_body}"

        # 1) status esperado
        if case.espera_status is not None and ev.response_status != case.espera_status:
            return (False,
                    f"Status esperado {case.espera_status}, obtido {ev.response_status}")

        # 2) campo esperado no corpo
        if case.espera_campo:
            body = ev.response_body if isinstance(ev.response_body, dict) else {}
            if case.espera_campo not in body:
                return False, f"Campo '{case.espera_campo}' ausente na resposta"

        # 3) regra de negocio especifica (ex.: desconto)
        if case.espera_regra:
            ok, motivo = self._avaliar_regra(case.espera_regra, ev)
            if not ok:
                return False, motivo

        return True, "Conforme o esperado"

    @staticmethod
    def _avaliar_regra(regra: str, ev: Evidence) -> tuple[bool, str]:
        body = ev.response_body if isinstance(ev.response_body, dict) else {}
        desconto = body.get("discount", None)
        if regra == "desconto_maior_que_zero":
            if desconto is None:
                return False, "Resposta sem campo 'discount'"
            if desconto <= 0:
                return False, f"Esperado desconto > 0, obtido {desconto}"
            return True, "Desconto aplicado corretamente"
        if regra == "desconto_igual_zero":
            if desconto is None:
                return False, "Resposta sem campo 'discount'"
            if desconto != 0:
                return False, f"Esperado desconto 0, obtido {desconto}"
            return True, "Sem desconto, conforme esperado"
        return True, "Regra sem validacao especifica"

    @staticmethod
    def _severidade(case: TestCase, ev: Evidence) -> str:
        # Falhas de seguranca/auth e conexao sao criticas
        if ev.response_status == 0:
            return settings.SEVERITY_CRITICAL
        if case.espera_status in (401, 403) or case.sem_auth:
            return settings.SEVERITY_CRITICAL
        # Erros de regra de calculo (desconto) sao altos
        if case.espera_regra:
            return settings.SEVERITY_HIGH
        # Divergencia de status 5xx inesperada
        if ev.response_status >= 500:
            return settings.SEVERITY_HIGH
        return settings.SEVERITY_MEDIUM
