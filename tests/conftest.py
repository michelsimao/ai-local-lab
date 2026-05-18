import os
import time
import subprocess
import requests
import pytest

# Fixture de sessão que sobe o Qdrant via docker-compose.test.yml e garante
# que tanto o Qdrant (container) quanto o Ollama (host) estejam prontos.


def wait_for_url(url, timeout=60, interval=1):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


@pytest.fixture(scope="session", autouse=True)
def integration_services():
    """Levanta Qdrant em container e garante que Ollama local esteja acessível.

    - Usa `docker compose -f docker-compose.test.yml up -d` para subir Qdrant.
    - Define variáveis de ambiente esperadas pela aplicação (`OLLAMA_BASE_URL`,
      `VECTOR_STORE_PROVIDER`, `QDRANT_URL`).
    - Aguarda os serviços responderem antes de ceder o controle aos testes.
    """
    compose_file = os.path.join(os.getcwd(), "docker-compose.test.yml")

    # Sobe os serviços de teste
    subprocess.run(["docker", "compose", "-f", compose_file, "up", "-d"], check=True)

    # Configura env para usar Ollama local e Qdrant do container
    os.environ["OLLAMA_BASE_URL"] = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    os.environ["VECTOR_STORE_PROVIDER"] = "qdrant"
    os.environ["QDRANT_URL"] = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")

    # Aguarda Ollama local
    if not wait_for_url(os.environ["OLLAMA_BASE_URL"], timeout=60):
        subprocess.run(["docker", "compose", "-f", compose_file, "down"])
        raise RuntimeError(f"Ollama not reachable at {os.environ['OLLAMA_BASE_URL']}")

    # Aguarda Qdrant readyz
    if not wait_for_url(f"{os.environ['QDRANT_URL']}/readyz", timeout=60):
        subprocess.run(["docker", "compose", "-f", compose_file, "down"])
        raise RuntimeError(f"Qdrant not ready at {os.environ['QDRANT_URL']}")

    yield

    # Teardown: derruba containers de teste
    subprocess.run(["docker", "compose", "-f", compose_file, "down"], check=True)
