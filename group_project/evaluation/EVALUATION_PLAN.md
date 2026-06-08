# Evaluation Plan

## Framework

RAGAS.

## Golden Dataset

`evaluation/golden_dataset.json` contains at least 15 cases:

- 10 Vietnamese drug-law questions.
- 5 related news or social-context questions.

Each case includes:

- `question`
- `expected_answer`
- `expected_context`
- `category`

## Metrics

- Faithfulness: whether the answer is supported by retrieved context.
- Answer relevancy: whether the answer addresses the question.
- Context recall: whether retrieved context covers the expected evidence.
- Context precision: whether retrieved context is useful rather than noisy.

## A/B Comparison

- `hybrid_rerank`: existing Task 9 retrieval with reranking.
- `hybrid_no_rerank`: same retrieval pipeline with reranking disabled.

## Report

`evaluation/results.md` should include:

- Overall scores by config.
- Metric deltas.
- Bottom 3 performers.
- Root-cause analysis.
- Recommendations.

## Minimum Acceptance

- Dataset loads successfully.
- Both configs run over all cases.
- RAGAS report is exported when dependencies and API keys are available.
- If RAGAS cannot run, the script still exports pipeline outputs and clear setup instructions.
