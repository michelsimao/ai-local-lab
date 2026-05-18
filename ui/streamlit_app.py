import streamlit as st
import httpx

API_DEFAULT = "http://localhost:8000"

st.set_page_config(page_title="AI Local Lab", page_icon="🤖", layout="centered")

st.title("AI Local Lab")
st.write(
    "Interface simples para ingerir textos e fazer perguntas com o agente RAG local "
    "(Ollama + Qdrant)."
)

api_url = st.text_input("API URL", API_DEFAULT)

st.markdown("---")

st.header("1. Ingestão de textos")
texts_input = st.text_area(
    "Cole textos ou frases aqui (uma entrada por linha).",
    height=180,
    placeholder="RAG significa Retrieval-Augmented Generation.\nLangGraph ajuda a orquestrar agentes.",
)

ingest_button = st.button("Ingerir textos")

if ingest_button:
    texts = [line.strip() for line in texts_input.splitlines() if line.strip()]
    if not texts:
        st.error("Adicione pelo menos um texto antes de ingerir.")
    else:
        try:
            with st.spinner("Ingerindo textos..."):
                # aumentar timeout para chamadas que podem demorar
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(f"{api_url}/ingest", json={"texts": texts})

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                st.error(f"Falha na ingestão (status={response.status_code}): {response.text}")
            else:
                data = response.json()
                st.success(f"Ingeridos {data.get('ingested', 0)} textos com sucesso.")
                st.write(data)
        except Exception as error:
            st.error(f"Erro ao conectar com a API: {error}")

st.markdown("---")

st.header("2. Fazer pergunta")
question = st.text_input("Pergunta", value="O que é RAG?")
chat_button = st.button("Enviar pergunta")

if chat_button:
    if not question.strip():
        st.error("Digite uma pergunta antes de enviar.")
    else:
        try:
            with st.spinner("Aguardando resposta do LLM... isso pode levar alguns segundos"):
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(f"{api_url}/chat", json={"question": question})

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                st.error(f"Falha no chat (status={response.status_code}): {response.text}")
            else:
                data = response.json()
                st.success("Resposta recebida com sucesso.")
                st.subheader("Pergunta")
                st.write(data.get("question"))
                st.subheader("Resposta")
                st.write(data.get("answer"))
                st.subheader("Contexto usado")
                st.write(data.get("context_used"))
                st.write(data)
        except Exception as error:
            st.error(f"Erro ao conectar com a API: {error}")

st.markdown("---")

st.caption(
    "A API deve estar rodando em segundo plano. Use `docker compose up --build` ou `make run` para iniciar o backend."
)
