# Fase 1 — Ambiente Local Completo para AI Infrastructure / Agent Engineering

## Objetivo

Construir um ambiente local profissional para desenvolvimento de:

- agentes de IA
- RAG
- workflows agênticos
- APIs IA
- observabilidade
- orquestração

Tudo rodando localmente, sem dependência inicial da AWS.

---

# Arquitetura Final

```text
┌───────────────────────┐
│      FastAPI API      │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│      LangGraph        │
│ Agent Orchestration   │
└──────────┬────────────┘
           │
 ┌─────────┴─────────┐
 ▼                   ▼
Ollama            Qdrant
LLM Local         Vector DB
           │
           ▼
        Floci
   Workflow Runtime
```

---

# Stack Tecnológica

| Ferramenta | Função |
|---|---|
| Docker | Infraestrutura |
| Docker Compose | Orquestração local |
| Ollama | LLM local |
| Qdrant | Banco vetorial |
| LangGraph | Sistema agêntico |
| FastAPI | API backend |
| Floci | Workflow engine |
| Python | Linguagem principal |

---

# Pré-requisitos

## 1. Instalar Docker

Site oficial:

https://www.docker.com/products/docker-desktop/

### Linux Mint (recomendado)

Instalar:

- Docker Engine
- Docker Compose plugin

### Verificar instalação

```bash
docker --version
docker compose version
```

---

## 2. Instalar Python

Recomendado:

- Python 3.11+

### Verificar

```bash
python3 --version
```

---

## 3. Instalar VSCode

https://code.visualstudio.com/

---

## 4. Extensões VSCode

Instale:

| Extensão | Objetivo |
|---|---|
| Python | suporte Python |
| Docker | containers |
| REST Client | testar APIs |
| Pylance | IntelliSense |
| GitLens | Git |
| Continue | IA local/opcional |

---

# Estrutura do Projeto

## Criar pasta

```bash
mkdir ai-local-lab
cd ai-local-lab
```

---

## Estrutura inicial

```text
ai-local-lab/
│
├── app/
│   ├── api/
│   ├── agents/
│   ├── workflows/
│   ├── services/
│   ├── vector/
│   └── main.py
│
├── data/
│
├── docker/
│
├── docker-compose.yml
│
├── Dockerfile
│
├── requirements.txt
│
└── .env
```

---

# PASSO 1 — Configurar Docker Compose

## Criar docker-compose.yml

```yaml
version: "3.9"

services:

  ollama:
    image: ollama/ollama
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  qdrant:
    image: qdrant/qdrant
    container_name: qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  fastapi:
    build: .
    container_name: fastapi
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - ollama
      - qdrant

volumes:
  ollama_data:
  qdrant_data:
```

---

# PASSO 2 — Criar Dockerfile

## Criar arquivo Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

# PASSO 3 — Configurar Python

## Criar requirements.txt

```txt
fastapi
uvicorn[standard]

langchain
langgraph

qdrant-client

ollama

pydantic

python-dotenv

httpx
```

---

# PASSO 4 — Criar API básica

## app/main.py

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "running"}
```

---

# PASSO 5 — Subir ambiente

## Executar

```bash
docker compose up --build
```

---

## Verificar containers

```bash
docker ps
```

Você deverá ver:

- ollama
- qdrant
- fastapi

---

# PASSO 6 — Testar FastAPI

Abrir:

```text
http://localhost:8000
```

Resultado esperado:

```json
{
  "status": "running"
}
```

---

# PASSO 7 — Configurar Ollama

## Entrar no container

```bash
docker exec -it ollama bash
```

---

## Baixar modelo

Exemplo:

```bash
ollama pull llama3
```

ou:

```bash
ollama pull mistral
```

---

## Testar

```bash
ollama run llama3
```

Digite:

```text
Hello
```

---

# PASSO 8 — Testar Ollama via API

## Criar arquivo

### app/services/llm.py

```python
import ollama

def ask_llm(prompt: str):

    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]
```

---

## Atualizar main.py

```python
from fastapi import FastAPI
from app.services.llm import ask_llm

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/ask")
async def ask(prompt: str):

    response = ask_llm(prompt)

    return {
        "response": response
    }
```

---

## Testar

Abrir:

```text
http://localhost:8000/ask?prompt=What%20is%20AI?
```

---

# PASSO 9 — Configurar Qdrant

## Testar painel

Abrir:

```text
http://localhost:6333/dashboard
```

---

## Criar integração vetorial

### app/vector/qdrant_client.py

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    host="qdrant",
    port=6333
)
```

---

# PASSO 10 — Configurar LangGraph

## Criar agente básico

### app/agents/basic_agent.py

```python
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.services.llm import ask_llm

class AgentState(TypedDict):
    input: str
    output: str

def run_agent(state):

    response = ask_llm(state["input"])

    return {
        "output": response
    }

graph = StateGraph(AgentState)

graph.add_node("llm", run_agent)

graph.set_entry_point("llm")

graph.add_edge("llm", END)

agent = graph.compile()
```

---

## Atualizar main.py

```python
from fastapi import FastAPI

from app.agents.basic_agent import agent

app = FastAPI()

@app.get("/agent")
async def run_agent(input: str):

    result = agent.invoke({
        "input": input
    })

    return result
```

---

## Testar

```text
http://localhost:8000/agent?input=Explain%20RAG
```

---

# PASSO 11 — Instalar Floci

## Repositório

https://github.com/floci-io/floci

---

## Clonar

```bash
git clone https://github.com/floci-io/floci.git
```

---

## Entrar na pasta

```bash
cd floci
```

---

## Subir ambiente

```bash
docker compose up
```

---

# Objetivo inicial com Floci

Você irá usar o Floci para:

- workflows
- agent pipelines
- runtime orchestration
- state management

---

# PASSO 12 — Integrar Tudo

Agora você começa a conectar:

| Origem | Destino |
|---|---|
| FastAPI | LangGraph |
| LangGraph | Ollama |
| LangGraph | Qdrant |
| Floci | LangGraph |
| FastAPI | Floci |

---

# PASSO 13 — Primeiro Projeto Real

## Objetivo

Criar:

- AI Agent
- com memória
- RAG
- tools
- workflow

---

## Features

### 1. Chat endpoint

```text
/chat
```

---

### 2. Memória vetorial

Qdrant.

---

### 3. Retrieval

Busca semântica.

---

### 4. Agent Router

LangGraph.

---

### 5. Workflow

Floci.

---

# O que você aprenderá nessa fase

## Infraestrutura

- Docker networking
- containers IA
- APIs distribuídas
- persistência vetorial

---

## IA

- inferência local
- embeddings
- retrieval
- agentes

---

## Arquitetura

- orchestration
- state machines
- workflows
- routing

---

## Backend

- FastAPI
- async
- APIs IA
- streaming

---

# Próxima fase ideal depois dessa

Quando isso estiver funcionando:

# Fase 2 — Hybrid Cloud AI

Migrar gradualmente:

| Local | AWS |
|---|---|
| Ollama | Bedrock |
| Qdrant | OpenSearch |
| Local workflow | Step Functions |
| Local events | EventBridge |
| Local auth | IAM |

---

# Recomendação importante

Não tente logo no começo:

- LangChain avançado
- multi-agent complexo
- fine tuning
- observabilidade avançada

---

# Ordem ideal de domínio

1. Docker
2. FastAPI
3. Ollama
4. Qdrant
5. LangGraph
6. Floci
7. RAG
8. Agents
9. Workflows
10. Observabilidade

---

# Repositórios e documentação

## Ollama

https://ollama.com/

---

## Qdrant

https://qdrant.tech/documentation/

---

## LangGraph

https://langchain-ai.github.io/langgraph/

---

## FastAPI

https://fastapi.tiangolo.com/

---

## Docker

https://docs.docker.com/

