"""
app.vector.vector_store_factory

Este módulo encapsula a criação/obtenção do vector store usado para armazenar
e recuperar documentos por similaridade. O comportamento é definido por
variáveis de ambiente para facilitar troca entre ambientes local e AWS.

Conceitos para iniciantes:
- Vector store (armazenamento vetorial): banco que indexa vetores (embeddings)
  para busca semântica.
- Collection / index: nome lógico onde os vetores são guardados.

Função principal:
- `get_vector_store(embeddings)`: retorna uma instância compatível com a
  interface de VectorStore do projeto.
"""

import os
from langchain_core.vectorstores import VectorStore


def get_vector_store(embeddings) -> VectorStore:
    """Cria ou retorna um vector store conforme variáveis de ambiente.

    Variáveis usadas:
    - `VECTOR_STORE_PROVIDER`: `qdrant` (local) ou `opensearch` (AWS).
    - `QDRANT_COLLECTION`: nome da coleção/index a ser usado.
    - `QDRANT_URL`: URL do serviço Qdrant (ex.: http://qdrant:6333).

    O parâmetro `embeddings` deve ser um objeto que converte texto em vetores
    (ex.: o retornado por `get_embeddings()` no `llm_factory`).
    """
    provider = os.getenv("VECTOR_STORE_PROVIDER", "qdrant")
    collection = os.getenv("QDRANT_COLLECTION", "ai_lab")

    if provider == "qdrant":
        # Usa Qdrant como armazenamento local.
        try:
            from langchain_qdrant import QdrantVectorStore
        except Exception:
            QdrantVectorStore = None

        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct

        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))

        # Cria a collection se não existir: Qdrant precisa de configuração de
        # tamanho do vetor e métrica de distância.
        existing = [c.name for c in client.get_collections().collections]
        if collection not in existing:
            # tamanho 384 é um valor comum para MiniLM; pode ser ajustado via env
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        if QdrantVectorStore is not None:
            return QdrantVectorStore(
                client=client,
                collection_name=collection,
                embedding=embeddings,
            )

        # Fallback simples: implementa a interface mínima usada no projeto
        class SimpleQdrantVectorStore:
            def __init__(self, client, collection_name, embedding):
                self.client = client
                self.collection_name = collection_name
                self.embedding = embedding
                self._id_counter = 0

            def add_texts(self, texts):
                # gera embeddings e faz upsert em Qdrant
                try:
                    vectors = self.embedding.embed_documents(texts)
                except Exception:
                    # fallback: tenta usar método alternativo
                    vectors = [self.embedding.embed_query(t) for t in texts]

                points = []
                for vec, text in zip(vectors, texts):
                    pid = self._id_counter
                    self._id_counter += 1
                    point = PointStruct(id=pid, vector=vec, payload={"text": text})
                    points.append(point)

                # upsert
                self.client.upsert(collection_name=self.collection_name, points=points)

            def as_retriever(self, search_kwargs=None):
                class Retriever:
                    def __init__(self, client, collection, embedding, k=3):
                        self.client = client
                        self.collection = collection
                        self.embedding = embedding
                        self.k = k

                    def invoke(self, query):
                        try:
                            qvec = self.embedding.embed_query(query)
                        except Exception:
                            qvec = self.embedding.embed_documents([query])[0]
                        results = self.client.search(
                            collection_name=self.collection,
                            query_vector=qvec,
                            limit=self.k,
                            with_payload=True,
                        )
                        # criar objetos com atributo page_content para compatibilidade
                        class Doc:
                            def __init__(self, text):
                                self.page_content = text

                        docs = [Doc(res.payload.get("text", "")) for res in results]
                        return docs

                k = 3
                if search_kwargs and "k" in search_kwargs:
                    k = search_kwargs["k"]
                return Retriever(client=self.client, collection=self.collection_name, embedding=self.embedding, k=k)

        return SimpleQdrantVectorStore(client=client, collection_name=collection, embedding=embeddings)

    if provider == "opensearch":
        # Usa OpenSearch (ex.: AWS OpenSearch Serverless) como vector store.
        from langchain_community.vectorstores import OpenSearchVectorSearch
        return OpenSearchVectorSearch(
            opensearch_url=os.getenv("OPENSEARCH_URL"),
            index_name=collection,
            embedding_function=embeddings,
            http_auth=None,           # autenticação via AWS SigV4 (geralmente)
            use_ssl=True,
            verify_certs=True,
            connection_class="RequestsHttpConnection",
        )

    raise ValueError(f"Vector store provider desconhecido: {provider}")