"""
Agente 2 - Designer.

Deriva casos de teste concretos a partir de cada regra de negocio e seus
criterios. Cada criterio vira um TestCase executavel, preservando o vinculo
com a regra de origem (rastreabilidade).
"""
from __future__ import annotations

from qa_crew.models import BusinessRule, TestCase


class Designer:
    nome = "Designer"
    papel = "Projeta casos de teste a partir das regras"

    def run(self, rules: list[BusinessRule]) -> list[TestCase]:
        cases: list[TestCase] = []
        for rule in rules:
            for idx, crit in enumerate(rule.criterios, start=1):
                case_id = f"{rule.id}-C{idx:02d}"
                cases.append(
                    TestCase(
                        id=case_id,
                        rule_id=rule.id,
                        nome=crit.get("nome", case_id),
                        endpoint=rule.endpoint,
                        metodo=rule.metodo,
                        payload=crit.get("payload"),
                        path_param=crit.get("path_param"),
                        espera_status=crit.get("espera_status"),
                        espera_campo=crit.get("espera_campo"),
                        espera_regra=crit.get("espera_regra"),
                        sem_auth=bool(crit.get("sem_auth", False)),
                        requer_login=bool(crit.get("requer_login", False)),
                        depende_de=crit.get("depende_de"),
                    )
                )
        return cases
