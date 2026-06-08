from __future__ import annotations

from pathlib import Path

import streamlit as st

from group_rag.rag_adapter import RAG_CONFIGS, answer_question


st.set_page_config(page_title="Drug Law RAG Chatbot", layout="wide")

GROUP_ROOT = Path(__file__).resolve().parent


def init_state() -> None:
    st.session_state.setdefault("messages", [])


def render_sources(sources: list[dict]) -> None:
    if not sources:
        st.info("No source documents were returned.")
        return

    for source in sources:
        title = (
            f"{source['rank']}. {source['label']} "
            f"({source['retrieval_source']}, score={source['score']:.3f})"
        )
        with st.expander(title):
            st.write(source["content"])
            if source.get("metadata"):
                st.json(source["metadata"], expanded=False)


init_state()

with st.sidebar:
    st.header("Config")
    config_name = st.selectbox(
        "RAG config",
        options=list(RAG_CONFIGS),
        format_func=lambda name: RAG_CONFIGS[name].label,
    )
    top_k = st.slider("Top K sources", min_value=2, max_value=8, value=5)
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Run evaluation:")
    st.code("python group_project/evaluation/eval_pipeline.py", language="bash")

st.title("Drug Law and News RAG Chatbot")
st.caption("Answers use retrieved evidence from the Task 9/10 RAG pipeline.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            render_sources(message["sources"])

prompt = st.chat_input("Ask about Vietnamese drug law or related news...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history = st.session_state.messages[:-1]
    with st.chat_message("assistant"):
        with st.spinner("Retrieving evidence and drafting an answer..."):
            result = answer_question(
                prompt,
                history=history,
                config_name=config_name,
                top_k=top_k,
            )
        st.markdown(result["answer"])
        st.caption(f"Config: {result['config_label']} | Model: {result['model']}")
        render_sources(result["sources"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "config": result["config"],
            "model": result["model"],
        }
    )
