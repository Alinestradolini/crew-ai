"""
Demo completa em um unico comando.

Sobe a API alvo mock em processo separado, aguarda ficar saudavel, executa
a QA Crew e abre o laudo HTML no navegador.

    python run_demo.py
"""
from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
BASE_URL = "http://localhost:8000"


def wait_health(timeout: float = 20.0) -> bool:
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=2.0)
            if r.status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    return False


def main() -> int:
    print(">> Subindo API alvo mock (uvicorn)...")
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "target_api.app:app",
         "--port", "8000", "--log-level", "warning"],
        cwd=str(ROOT),
    )
    try:
        if not wait_health():
            print("!! API nao respondeu ao health check. Abortando.")
            return 1
        print(">> API saudavel. Executando QA Crew...\n")

        from qa_crew.crew import QACrew
        crew = QACrew(base_url=BASE_URL)
        report = crew.run()
        html_path, _ = crew.save(report)

        print("\n>> Abrindo laudo no navegador...")
        webbrowser.open(Path(html_path).resolve().as_uri())
        return 0
    finally:
        print(">> Encerrando API alvo...")
        api.terminate()
        try:
            api.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api.kill()


if __name__ == "__main__":
    raise SystemExit(main())
