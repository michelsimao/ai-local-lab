"""
app.agents.rag_agent

Este módulo implementa um agente simples de RAG (Retrieval-Augmented
Generation) usando LangGraph para orquestrar passos em um grafo de estados.

Explicação para iniciantes:
- RAG combina recuperação de documentos (retrieval) com geração de texto
  (generation) usando um LLM.
- LangGraph permite definir nós (funções) e as transições entre eles,
  criando um fluxo de execução claro.

Componentes principais:
- `AgentState`: tipo que descreve os dados que o agente carrega entre nós.
- `retrieve`: função que consulta o vector store e preenche o contexto.
- `generate`: função que monta um prompt com contexto e chama o LLM.
- `rag_agent`: objeto compilado do grafo que pode ser invocado pelo API.
"""

from typing import TypedDict, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.services.llm_factory import get_llm, get_embeddings
from app.vector.vector_store_factory import get_vector_store


# ── Estado do agente ──────────────────────────────────────────────────

class AgentState(TypedDict):
    """Tipo que representa o estado compartilhado entre nós do grafo.

    - `question`: a pergunta que o usuário fez.
    - `context`: lista de trechos de texto recuperados do vector store.
    - `answer`: resposta gerada pelo LLM.
    """
    question: str
    context: List[str]
    answer: str


# ── Instâncias (criadas uma vez, reutilizadas) ────────────────────────
# Criamos as instâncias do LLM, embeddings e do vector store uma vez para
# reutilização entre requisições (economiza tempo e recursos).
llm = get_llm()
embeddings = get_embeddings()
vector_store = get_vector_store(embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})


# ── Nós do grafo ─────────────────────────────────────────────────────

def retrieve(state: AgentState) -> AgentState:
    """Busca os documentos mais relevantes para a pergunta.

    - Recebe o `state` com pelo menos a chave `question`.
    - Usa o `retriever` (baseado no vector store) para obter documentos.
    - Retorna um novo estado com o campo `context` preenchido.
    """
    docs = retriever.invoke(state["question"])
    context = [doc.page_content for doc in docs]
    return {**state, "context": context}


def generate(state: AgentState) -> AgentState:
    """Gera uma resposta usando o LLM e o contexto recuperado.

    - Cria um `ChatPromptTemplate` que inclui o contexto e a pergunta.
    - Junta o prompt com o `llm` para formar uma cadeia (`chain`).
    - Invoca a cadeia e retorna o estado atualizado com `answer`.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Você é um assistente útil. "
            "Use o contexto abaixo para responder a pergunta. "
            "Se não souber, diga que não sabe.\n\n"
            "Contexto:\n{context}"
        )),
        ("human", "{question}"),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "context": "\n\n".join(state["context"]),
        "question": state["question"],
    })

    return {**state, "answer": response.content}


# ── Grafo ─────────────────────────────────────────────────────────────

# Definimos o grafo de execução: primeiro `retrieve`, depois `generate`,
# e em seguida terminamos (END). O `rag_agent` é o objeto compilado.
graph = StateGraph(AgentState)

graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)

rag_agent = graph.compile()