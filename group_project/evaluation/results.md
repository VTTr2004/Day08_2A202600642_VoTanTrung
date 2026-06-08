# RAG Evaluation Results

Generated: 2026-06-08 16:24:21

## Framework

RAGAS

## Dataset

- Total cases: 15
- Split: 10 law cases, 5 news/context cases

## Overall Scores

| Metric | Hybrid retrieval + MMR reranking | Hybrid retrieval without reranking | Delta A-B |
|---|---|---|---|
| faithfulness | n/a | n/a | n/a |
| answer_relevancy | n/a | n/a | n/a |
| context_recall | n/a | n/a | n/a |
| context_precision | n/a | n/a | n/a |
| average | n/a | n/a | n/a |

## A/B Comparison

- Config A: Hybrid retrieval with MMR reranking.
- Config B: Hybrid retrieval without reranking.

## Evaluation Status

RAGAS did not complete for at least one config. Pipeline outputs were still saved to `raw_outputs.json`.

### hybrid_rerank

Error: `No module named 'langchain_community.chat_models.vertexai'`

### hybrid_no_rerank

Error: `No module named 'langchain_community.chat_models.vertexai'`

## Worst Performers

| # | Question | Faithfulness | Relevance | Recall | Precision |
|---|---|---|---|---|---|
| 1 | n/a - run RAGAS with required dependencies/API keys | n/a | n/a | n/a | n/a |

## Recommendations

1. Improve chunk metadata so citations show legal article, source title, and year more consistently.
2. Add query rewriting for short follow-up questions before retrieval.
3. Review bottom cases and add domain-specific synonyms for Vietnamese legal terms.

## Raw Outputs

`raw_outputs.json` contains generated answers and retrieved contexts for each config.
