"""
app.main

Este arquivo define a API web mínima do projeto usando FastAPI. Ele expõe
rotas simples para checar o estado do serviço (`/health`), ingerir textos
no vector store (`/ingest`) e fazer perguntas usando um agente RAG
(`/chat`).

Para um iniciante em Python:
- FastAPI é um framework web leve que permite definir "rotas" como funções.
- `Pydantic` é usado para validar e tipar os dados de entrada (models).
- Funções assíncronas (`async def`) são recomendadas em FastAPI para I/O.

Este arquivo importa funções de fábrica para o LLM e o armazenamento vetorial,
e usa o `rag_agent` para orquestrar a lógica de RAG.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from app.agents.rag_agent import rag_agent
from app.services.llm_factory import get_embeddings
from app.vector.vector_store_factory import get_vector_store

app = FastAPI(title="AI Local Lab", version="1.0.0")


# ── Schemas ───────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """Schema para requisições de pergunta.

    - `question`: texto com a pergunta do usuário.

    Usamos `pydantic.BaseModel` para garantir que a entrada tenha o formato
    esperado. FastAPI converte automaticamente o JSON recebido para essa
    classe antes de passar para a função de rota.
    """
    question: str


class IngestRequest(BaseModel):
    """Schema para requisições de ingestão de textos.

    - `texts`: lista de strings que serão transformadas em embeddings e
      adicionadas ao vector store.
    """
    texts: List[str]


# ── Rotas ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Rota de saúde simples.

    Retorna um JSON com o status do serviço. Útil para checagens de
    disponibilidade (health checks) em orquestradores ou reverse proxies.
    """
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: QuestionRequest):
    """Faz uma pergunta ao agente RAG e retorna a resposta.

    Fluxo simplificado:
    1. Recebe uma `QuestionRequest` com a pergunta.
    2. Invoca o `rag_agent` (definido em `app.agents.rag_agent`).
    3. Retorna a resposta junto com quantos documentos de contexto foram usados.

    Observação para iniciantes: o agente realiza recuperação (retrieval)
    dos documentos relevantes no vector store e usa o LLM para gerar a resposta.
    """
    try:
        result = rag_agent.invoke({"question": req.question, "context": [], "answer": ""})
        return {
            "question": result["question"],
            "answer": result["answer"],
            "context_used": len(result["context"]),
        }
    except Exception as e:
        message = str(e)
        if "ollama call failed" in message.lower() or "model is not found" in message.lower():
            raise HTTPException(
                status_code=500,
                detail=(
                    "Ollama não encontrou o modelo configurado. "
                    "Verifique `LLM_MODEL` em `.env` e instale ou faça pull do modelo localmente. "
                    "Exemplo: `ollama pull llama3`."
                ),
            )
        raise HTTPException(status_code=500, detail=message)


@app.post("/ingest")
async def ingest(req: IngestRequest):
    """Ingesta uma lista de textos no vector store.

    Passos executados:
    1. Obtém a função de embeddings via `get_embeddings()`.
    2. Constrói/obtém o vector store via `get_vector_store(embeddings)`.
    3. Chama `vector_store.add_texts(...)` para armazenar os textos.

    Retorna o número de textos ingeridos.
    """
    try:
        embeddings = get_embeddings()
        vector_store = get_vector_store(embeddings)
        vector_store.add_texts(req.texts)
        return {"ingested": len(req.texts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))