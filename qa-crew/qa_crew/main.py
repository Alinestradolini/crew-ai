"""
Ponto de entrada da QA Crew.

Uso:
    python -m qa_crew.main --base-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import sys

from config import settings
from qa_crew.crew import QACrew


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QA Crew - testes autonomos de API")
    parser.add_argument("--base-url", default=settings.DEFAULT_BASE_URL,
                        help="URL base da API alvo")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    crew = QACrew(base_url=args.base_url)
    report = crew.run()
    crew.save(report)
    # codigo de saida != 0 se houver nao conformidade critica/alta (util em CI)
    nc = report.indicadores["nao_conformidades"]
    return 1 if (nc["critica"] + nc["alta"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
