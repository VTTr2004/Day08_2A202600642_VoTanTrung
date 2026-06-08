# Decision Log

## 2026-06-08

| Decision | Rationale |
|---|---|
| Build combo chatbot + evaluation pipeline | Gives a stronger group deliverable than only one side of the assignment. |
| Use Level 2 | The project needs structured docs, logs, evaluation, and reusable wrappers but not deployment. |
| Use Streamlit | Fast local demo UI for chat, memory, and source inspection. |
| Use RAGAS | User selected RAGAS for RAG evaluation. |
| Reuse Task 9 and Task 10 | Keeps the group project focused on integration, UI, evaluation, and reporting. |
| Compare reranking vs no reranking | Directly tests whether the retrieval pipeline improvement helps. |
| Configure Gemini through env vars | Avoids hardcoding secrets or model names and keeps fallback behavior available. |
