# AI Local Lab

Um ambiente local para desenvolver agentes de IA, RAG (Retrieval-Augmented Generation),
workflows e APIs com foco em uso local (Ollama + Qdrant) e fácil migração para AWS.

Este README explica o propósito do projeto, a estrutura do código, como rodar localmente
e como executar testes — tudo explicado de forma didática para iniciantes.

---

## Visão geral

O objetivo deste repositório é oferecer um ambiente de desenvolvimento completo e
reprodutível para experimentar com agentes e pipelines de IA locais. A arquitetura
usa:

- Ollama: LLM local (já pode estar instalado no host).
- Qdrant: banco vetorial para embeddings.
- FastAPI: API HTTP que expõe rotas para ingestão e chat.
- LangGraph / LangChain: orquestração e integração com LLMs.

Tudo é organizado para que a transição para serviços na nuvem (por exemplo, Bedrock
e OpenSearch) demande apenas alteração em variáveis de ambiente.

---

## Estrutura do código

Explicação dos arquivos e pastas principais:

- `app/`
  - `main.py` — aplicação FastAPI que expõe as rotas `/health`, `/ingest` e `/chat`.
  - `agents/` — código dos agentes; contém `rag_agent.py` (grafo RAG com LangGraph).
  - `services/` — fábricas e adaptadores de LLMs (`llm_factory.py`).
  - `vector/` — fábrica do vector store (`vector_store_factory.py`) e integração com Qdrant/OpenSearch.
  - `api/` e `workflows/` — pastas preparadas para expansão.

- `docker-compose.yaml` — composição dos serviços para desenvolvimento (Qdrant e FastAPI; usa Ollama local do host).
- `Dockerfile` — imagem para rodar a API em container.
- `requirements.txt` — dependências Python.
- `.env.example` — exemplo de variáveis de ambiente.

- `tests/` — testes unitários e de integração:
  - `tests/test_api.py` — testes unitários que usam dummies/mocks para dependências.
  - `tests/conftest.py` — fixtures para testes de integração (sobe Qdrant e espera Ollama).
  - `tests/integration/` — testes de integração que usam Ollama local + Qdrant em container.

---

## Variáveis de ambiente principais

Copie `.env.example` para `.env` e ajuste quando necessário:

- `LLM_PROVIDER` — `ollama` (local) ou `bedrock` (AWS).
- `LLM_MODEL` — identificador do modelo (ex.: `llama3`).
- `OLLAMA_BASE_URL` — URL do Ollama local (ex.: `http://127.0.0.1:11434`).
- `EMBEDDING_PROVIDER` — `sentence_transformers` (local) ou `bedrock` (AWS).
- `EMBEDDING_MODEL` — modelo de embeddings (ex.: `all-MiniLM-L6-v2`).
- `VECTOR_STORE_PROVIDER` — `qdrant` (local) ou `opensearch` (AWS).
- `QDRANT_URL` — URL do Qdrant (`http://127.0.0.1:6333`).
- `QDRANT_COLLECTION` — nome da coleção de vetores (ex.: `ai_lab`).

As variáveis estão documentadas em `.env.example` criado no repositório.

---

## Requisitos (pré-requisitos)

- Docker e Docker Compose (para Qdrant em testes/integrations)
- Python 3.11+ (recomendado)
- Ollama instalado localmente (opcional — pode usar container se preferir)

---

## Quickstart — rodando localmente

1. Copie o exemplo de `.env`:

```bash
cp .env.example .env
# (edite .env se necessário)
```

2. Crie e ative um virtualenv e instale dependências:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

3. Garanta que o Ollama está rodando no host (ex.: `ollama list` mostra modelos).

   Se você usar `LLM_MODEL=llama3`, certifique-se de ter o modelo instalado localmente:

   ```bash
   ollama pull llama3
   ```

4. Suba os serviços de desenvolvimento. Este Compose inicia o FastAPI e o Qdrant; o Ollama deve estar disponível localmente no host.

```bash
docker compose up --build
```

5. Rode a interface Streamlit para usar a aplicação via browser:

```bash
streamlit run ui/streamlit_app.py
```

6. Rode a API localmente (quando o ambiente estiver pronto):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000/docs` para ver a documentação automática do FastAPI.

---

## Exemplos com curl

### Ingestão de textos

Envia uma lista de textos para ser adicionada ao vector store:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"texts": ["RAG significa Retrieval-Augmented Generation.", "LangGraph ajuda a orquestrar agentes."]}'
```

### Perguntar ao agente RAG

Faz uma pergunta e obtém a resposta gerada com base no contexto:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "O que é RAG?"}'
```

---

## Testes

Existem dois tipos de testes:

- Unitários (rápidos): `tests/test_api.py` — usam dummies para não depender de serviços externos.
- Integração (mais lentos): `tests/integration/*` — usam Ollama local e sobem Qdrant em container.

Comandos úteis:

```bash
# Rodar todos os testes rápidos
.venv/bin/python -m pytest -q

# Rodar apenas testes de integração (certifique-se de que Ollama está rodando localmente)
export OLLAMA_BASE_URL=http://127.0.0.1:11434
.venv/bin/python -m pytest tests/integration -q
```

O `tests/conftest.py` usa `docker compose -f docker-compose.test.yml up -d` para subir
o Qdrant de teste e espera tanto Qdrant quanto Ollama estarem prontos antes de importar
o módulo `app.main` (assim a aplicação inicializa com serviços disponíveis).

---

## Makefile

Criamos um `Makefile` com comandos úteis para acelerar os passos mais comuns.

- `make install` — cria o virtualenv e instala as dependências.
- `make run` — executa a API local com uvicorn.
- `make test` — roda todos os testes unitários.
- `make integration` — roda os testes de integração que usam Ollama local e Qdrant de teste.
- `make clean` — limpa o ambiente virtual e arquivos gerados.

Use os comandos abaixo:

```bash
make install
make run
make test
make integration
make clean
```

---

## Notas técnicas importantes (para iniciantes)

- `app/main.py` importa e cria instâncias do agente e do vector store durante
  a importação do módulo. Por isso, em testes unitários nós usamos "dummies"
  (módulos substitutos) para evitar inicializações pesadas e dependências externas.

- Para testes de integração, o repositório contém `docker-compose.test.yml` que sobe
  somente o Qdrant. Como você informou que já tem o Ollama no host, os testes de
  integração usam o Ollama local automaticamente (variável `OLLAMA_BASE_URL`).

- Implementamos um fallback simples (`SimpleQdrantVectorStore`) em
  `app/vector/vector_store_factory.py` que oferece a funcionalidade mínima
  necessária caso a dependência `langchain_qdrant.QdrantVectorStore` não
  esteja disponível. Esse fallback é útil para execução de testes locais,
  mas para produção recomenda-se usar a implementação oficial.

---

## Fluxo de desenvolvimento sugerido

1. Trabalhe iterativamente com testes unitários primeiro (`tests/test_api.py`).
2. Antes de integrar mudanças que toquem armazenamento vetorial ou LLM, rode
   os testes de integração (`tests/integration/`).
3. Se for executar em CI, configure um job separado para testes de integração
   com Docker (marque eles como `integration` se quiser filtrar com pytest markers).

---

## Próximos passos e melhorias sugeridas

- Adicionar mais testes de integração cobrindo `/ingest` e `/chat` com dados reais.
- Remover o fallback quando a versão do `langchain_qdrant` for atualizada.
- Adicionar scripts de manutenção para limpar coleções de teste do Qdrant.

---
