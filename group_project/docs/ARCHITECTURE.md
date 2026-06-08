# Architecture

## Level

Level 2 - Structured Agent.

## System Overview

```text
Streamlit app
  -> group_project/group_rag/rag_adapter.py
  -> src/task10_generation.py
  -> src/task9_retrieval_pipeline.py
  -> Task 5 semantic + Task 6 lexical + Task 7 reranking + Task 8 fallback
  -> answer + citations + sources
```

## Components

### Streamlit UI

`group_project/app.py` provides the chat interface, conversation memory, config controls, and source document display.

### RAG Adapter

`group_project/group_rag/rag_adapter.py` is the thin project-specific wrapper. It:

- Adds the project root to `sys.path`.
- Builds a standalone question from recent chat turns for follow-up questions.
- Calls the existing generation pipeline.
- Supports A/B retrieval configs used by evaluation.
- Normalizes source metadata for UI and reports.

### Existing AI Core

The project reuses:

- `src/task9_retrieval_pipeline.py` for retrieval.
- `src/task10_generation.py` for cited generation.

Generation is configured through environment variables. The selected model is Gemini 3.1 Flash Lite when a Gemini API key is available; otherwise the existing extractive fallback keeps the demo runnable.

### Evaluation

`group_project/evaluation/eval_pipeline.py` loads `golden_dataset.json`, runs each RAG config, evaluates with RAGAS, and writes `results.md`.

## A/B Configs

- Config A: hybrid retrieval with reranking.
- Config B: hybrid retrieval without reranking.

## Logging And Handoff

- `docs/WORKLOG.md` records implementation progress.
- `docs/DECISION_LOG.md` records key decisions.
- `evaluation/results.md` records evaluation output and failure analysis.

## Limitations

- RAGAS metrics usually require an LLM provider key.
- Retrieval quality depends on the local indexed corpus from earlier tasks.
- Gemini model naming is environment-configurable to avoid hardcoding SDK-specific names.
