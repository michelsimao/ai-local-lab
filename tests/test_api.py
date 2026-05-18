import sys
import types
from types import SimpleNamespace

# Antes de importar `app.main`, injetamos módulos dummy para evitar que os
# módulos reais executem inicializações pesadas (Qdrant, SentenceTransformers, etc.)
dummy_llm = types.ModuleType("app.services.llm_factory")
dummy_llm.get_embeddings = lambda: None
dummy_llm.get_llm = lambda: None
sys.modules["app.services.llm_factory"] = dummy_llm

dummy_vector = types.ModuleType("app.vector.vector_store_factory")
class DummyVS:
    def as_retriever(self, search_kwargs=None):
        class R:
            def invoke(self, q):
                return []
        return R()
dummy_vector.get_vector_store = lambda emb: DummyVS()
sys.modules["app.vector.vector_store_factory"] = dummy_vector

dummy_rag = types.ModuleType("app.agents.rag_agent")
dummy_rag.rag_agent = SimpleNamespace(invoke=lambda state: {"question": state.get("question"), "answer": "fake", "context": []})
sys.modules["app.agents.rag_agent"] = dummy_rag

from fastapi.testclient import TestClient
import app.main as main


client = TestClient(main.app)


def test_health():
    """Verifica resposta da rota /health."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ingest(monkeypatch):
    """Testa /ingest mockando embeddings e o vector store.

    Substituímos `get_embeddings` e `get_vector_store` no módulo `app.main`
    por versões simples para evitar dependências externas durante o teste.
    """

    class DummyVectorStore:
        def __init__(self):
            self.added = []

        def add_texts(self, texts):
            # Apenas armazena os textos para verificação
            self.added.extend(texts)

    # Monkeypatch das fábricas usadas por app.main
    monkeypatch.setattr(main, "get_embeddings", lambda: None)
    monkeypatch.setattr(main, "get_vector_store", lambda emb: DummyVectorStore())

    resp = client.post("/ingest", json={"texts": ["doc1", "doc2"]})
    assert resp.status_code == 200
    assert resp.json().get("ingested") == 2


def test_chat(monkeypatch):
    """Testa /chat mockando o `rag_agent.invoke` para resposta previsível."""

    def fake_invoke(state):
        return {"question": state["question"], "answer": "resposta-teste", "context": ["c1", "c2"]}

    # Substitui o rag_agent por um objeto simples com método invoke
    monkeypatch.setattr(main, "rag_agent", SimpleNamespace(invoke=fake_invoke))

    resp = client.post("/chat", json={"question": "Qual é o teste?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "Qual é o teste?"
    assert data["answer"] == "resposta-teste"
    assert data["context_used"] == 2
