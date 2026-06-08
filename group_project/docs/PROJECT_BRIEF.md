# Project Brief

## Project

Drug Law and News RAG Chatbot with RAGAS Evaluation.

## Goal

Build a local demo chatbot that answers questions about Vietnamese drug law and related news using the existing Task 9 retrieval pipeline and Task 10 citation generation pipeline. The project also includes a RAGAS evaluation pipeline with a 15-case golden dataset and A/B comparison.

## Target Users

- Course instructors reviewing the group project.
- Students demonstrating a RAG workflow.
- Demo users asking questions about drug law and related news.

## User-Facing Behavior

- Ask a question in a Streamlit chat UI.
- Receive a Vietnamese answer with citations.
- Ask follow-up questions using the recent conversation as memory.
- Inspect the source documents used by the answer.
- Run an evaluation script to compare at least two RAG configs.

## Success Criteria

- Streamlit app runs locally.
- Chatbot calls the existing retrieval/generation core.
- Source documents are shown for every answer.
- Golden dataset contains at least 15 Q&A cases.
- RAGAS evaluation script builds datasets for A/B configs and exports a report.
- Worklog and decision log are updated for handoff.

## Non-Goals

- Production deployment.
- Authentication.
- Docker or CI/CD.
- Persistent database.
- Complex frontend beyond Streamlit.
