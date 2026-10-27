"""Modelos de dados compartilhados entre os agentes da Crew."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BusinessRule:
    """Regra de negocio interpretada a partir da documentacao."""
    id: str
    titulo: str
    descricao: str
    endpoint: str
    metodo: str
    criterios: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TestCase:
    """Caso de teste derivado de uma regra de negocio."""
    id: str
    rule_id: str
    nome: str
    endpoint: str
    metodo: str
    payload: Optional[dict[str, Any]] = None
    path_param: Optional[dict[str, Any]] = None
    espera_status: Optional[int] = None
    espera_campo: Optional[str] = None
    espera_regra: Optional[str] = None
    sem_auth: bool = False
    requer_login: bool = False
    depende_de: Optional[str] = None


@dataclass
class Evidence:
    """Evidencia da execucao de um caso de teste."""
    request_method: str
    request_url: str
    request_body: Any
    response_status: int
    response_body: Any
    elapsed_ms: float


@dataclass
class TestResult:
    """Resultado da avaliacao de um caso de teste."""
    case: TestCase
    passou: bool
    motivo: str
    severidade: Optional[str] = None
    evidencia: Optional[Evidence] = None


@dataclass
class QAReport:
    """Laudo tecnico consolidado."""
    rules: list[BusinessRule]
    results: list[TestResult]
    indicadores: dict[str, Any] = field(default_factory=dict)
    recomendacoes: list[str] = field(default_factory=list)
    modo_llm: str = "offline"
    base_url: str = ""
