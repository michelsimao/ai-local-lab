# AI Local Lab — Guia Corrigido (com foco em AWS)

## Princípio central

> Cada serviço local tem um equivalente direto na AWS.  
> O código **não muda** na migração — só a variável de ambiente.

---

## Mapa Local → AWS

| Camada | Local (Fase 1) | AWS (Fase 2) |
|---|---|---|
| LLM | Ollama (llama3, mistral) | Amazon Bedrock (Titan, Claude, Llama) |
| Embeddings | sentence-transformers | Amazon Titan Embeddings |
| Vector Store | Qdrant | OpenSearch Serverless ou Aurora pgvector |
| API | FastAPI + Docker | ECS Fargate ou Lambda + API Gateway |
| Orquestração | LangGraph local | LangGraph + Step Functions |
| Observabilidade | LangSmith (free) | CloudWatch + X-Ray |
| Infraestrutura | Docker Compose | CDK ou Terraform |

---

## Estrutura do projeto

```
ai-local-lab/
│
├── app/
│   ├── agents/
│   │   └── rag_agent.py          ← LangGraph com RAG
│   ├── services/
│   │   └── llm_factory.py        ← abstração Ollama / Bedrock
│   ├── vector/
│   │   └── vector_store_factory.py  ← abstração Qdrant / OpenSearch
│   └── main.py                   ← FastAPI
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env                          ← copiar de .env.example
```

---

## Passo a passo

### 1. Clonar e configurar

```bash
mkdir ai-local-lab && cd ai-local-lab
cp .env.example .env
```

### 2. Subir o ambiente

```bash
docker compose up --build
```

Os containers só sobem quando Ollama e Qdrant estão prontos
(health checks garantem isso).

### 3. Baixar modelo no Ollama

```bash
docker exec -it ollama ollama pull llama3
```

### 4. Verificar serviços

| Serviço | URL |
|---|---|
| FastAPI docs | http://localhost:8000/docs |
| Qdrant dashboard | http://localhost:6333/dashboard |
| Ollama API | http://localhost:11434 |

### 5. Testar o pipeline completo

**Ingerir texto:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"texts": ["RAG significa Retrieval-Augmented Generation.", "LangGraph é um framework para agentes."]}'
```

**Fazer pergunta com RAG:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "O que é RAG?"}'
```

---

## Migração para AWS (Fase 2)

Só precisa mudar o `.env`:

```env
# Fase 1 (local)
LLM_PROVIDER=ollama
VECTOR_STORE_PROVIDER=qdrant

# Fase 2 (AWS) — apenas isso muda
LLM_PROVIDER=bedrock
LLM_MODEL=amazon.titan-text-express-v1
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.titan-embed-text-v1
VECTOR_STORE_PROVIDER=opensearch
OPENSEARCH_URL=https://xxxx.us-east-1.aoss.amazonaws.com
AWS_REGION=us-east-1
```

O código da API e dos agentes **não muda**.

---

## Por que o Floci foi removido?

O documento original recomendava Floci como workflow engine,
mas a ferramenta tem pouca adoção e documentação imatura.

**O LangGraph já cobre tudo o que o Floci propunha:**
- State machines para agentes
- Pipelines com branches e loops
- Persistência de estado (via checkpointers)

Para workflows mais complexos na AWS, use **Step Functions**
(que o LangGraph pode chamar nativamente via boto3).

---

## Próximos passos sugeridos

1. **Adicionar memória** — LangGraph com `SqliteSaver` local → `DynamoDB` na AWS  
2. **Adicionar tools** — LangGraph ToolNode com funções Python  
3. **Streaming** — FastAPI `StreamingResponse` + LangGraph `.astream()`  
4. **Observabilidade** — ativar LangSmith no `.env` para rastrear chamadas  
5. **Deploy AWS** — ECS Fargate com task definition + ALB  
