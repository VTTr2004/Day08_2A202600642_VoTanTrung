# Group Project - Drug Law RAG Chatbot

This group project combines both assignment directions:

- Streamlit RAG chatbot for Vietnamese drug law and related news.
- RAGAS evaluation pipeline with a 15-case golden dataset and A/B comparison.

## Architecture

```text
group_project/app.py
  -> group_project/group_rag/rag_adapter.py
  -> ../src/task10_generation.py
  -> ../src/task9_retrieval_pipeline.py
  -> retrieval sources + cited answer
```

## Files

```text
group_project/
  app.py
  group_rag/
    rag_adapter.py
  docs/
    PROJECT_BRIEF.md
    ARCHITECTURE.md
    DECISION_LOG.md
    WORKLOG.md
  evaluation/
    EVALUATION_PLAN.md
    golden_dataset.json
    eval_pipeline.py
    results.md
```

## Setup

From the project root:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set Gemini if available:

```text
GEMINI_API_KEY=...
GEMINI_GENERATION_MODEL=gemini-3.1-flash-lite
RAGAS_GEMINI_MODEL=gemini-3.1-flash-lite
```

The chatbot still runs with the extractive fallback when no LLM key is configured.

## Run Chatbot

```bash
streamlit run group_project/app.py
```

## Run Evaluation

```bash
python group_project/evaluation/eval_pipeline.py
```

Outputs:

- `group_project/evaluation/results.md`
- `group_project/evaluation/raw_outputs.json`

## A/B Configs

- `hybrid_rerank`: hybrid retrieval plus MMR reranking.
- `hybrid_no_rerank`: hybrid retrieval without reranking.

## Notes

RAGAS metrics require compatible dependencies and an LLM provider key. If RAGAS cannot run, the evaluation script still exports raw pipeline outputs and writes the setup issue into `results.md`.
