"""
app.services.llm_factory

Este módulo contém funções que criam as instâncias de LLM (modelo de
linguagem) e embeddings usados pelo projeto. A ideia é permitir trocar o
"provider" (por exemplo, `ollama` local ou `bedrock` na AWS) apenas mudando
variáveis de ambiente, sem alterar o código que consome o LLM.

Conceitos para iniciantes:
- Provider: implementação que fornece o serviço (ex.: Ollama, Bedrock).
- Modelo/ID do modelo: identifica qual modelo de linguagem usar (ex.: llama3).
- Embeddings: representação numérica de textos usada para busca semântica.

Funções exportadas:
- `get_llm()`: retorna uma instância do chat model configurado.
- `get_embeddings()`: retorna um objeto que calcula embeddings.
"""

import os
from langchain_core.language_models.chat_models import BaseChatModel


def get_llm() -> BaseChatModel:
    """Cria e retorna um modelo de chat (LLM) configurado por variáveis.

    Procura as variáveis de ambiente:
    - `LLM_PROVIDER`: `ollama` (local) ou `bedrock` (AWS).
    - `LLM_MODEL`: identificador do modelo (ex.: `llama3`).

    Retorna uma instância compatível com a interface do projeto.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model = os.getenv("LLM_MODEL", "mistral:latest")

    if provider == "ollama":
        # ChatOllama conversa com o servidor Ollama local via HTTP.
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=model,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        )

    if provider == "bedrock":
        # ChatBedrock usa a integração AWS Bedrock via boto3/SDK.
        from langchain_aws import ChatBedrock
        return ChatBedrock(
            model_id=model,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    raise ValueError(f"Provider desconhecido: {provider}")


def get_embeddings():
    """Retorna o objeto de embeddings configurado por variáveis.

    Variáveis usadas:
    - `EMBEDDING_PROVIDER`: `sentence_transformers` ou `bedrock`.
    - `EMBEDDING_MODEL`: nome do modelo de embeddings.

    O objeto retornado possui um método para transformar texto em vetores,
    que é usado pelo vector store para indexação e busca.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
    model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    if provider == "sentence_transformers":
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        return SentenceTransformerEmbeddings(model_name=model)

    if provider == "bedrock":
        from langchain_aws import BedrockEmbeddings
        return BedrockEmbeddings(
            model_id=model,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    raise ValueError(f"Embedding provider desconhecido: {provider}")