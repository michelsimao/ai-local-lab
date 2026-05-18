import importlib
from fastapi.testclient import TestClient


def test_app_health_integration():
    """Importa `app.main` após os serviços de integração estarem prontos
    (a fixture em `tests/conftest.py` garante isso) e verifica `/health`.
    """
    # Importa o módulo apenas quando o teste roda (não na coleta)
    app_module = importlib.import_module("app.main")
    client = TestClient(app_module.app)

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
