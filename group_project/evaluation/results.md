# RAG Evaluation Results

Generated: 2026-06-08

## Evaluation Source

This report is written from `raw_outputs.json`, which contains generated answers and retrieved contexts for both A/B configs.

RAGAS did not produce official metric scores in this local run because the environment is missing a LangChain community dependency:

```text
No module named 'langchain_community.chat_models.vertexai'
```

Therefore, the numeric table below uses lightweight proxy checks computed from the raw outputs:

- Answer keyword coverage: overlap between `expected_answer` keywords and generated answer keywords.
- Expected-context coverage: overlap between `expected_context` keywords and retrieved context keywords.
- Proxy score: `0.6 * answer_keyword_coverage + 0.4 * expected_context_coverage`.

These proxy scores are useful for debugging retrieval/generation behavior, but they should not be presented as official RAGAS scores.

## Dataset

- Total cases: 15
- Law cases: 10
- News/context cases: 5
- Models used in raw output: `extractive_fallback`

## Overall Proxy Scores

| Metric | Config A: hybrid + rerank | Config B: hybrid no rerank | Delta A-B |
|---|---:|---:|---:|
| Answer keyword coverage | 0.340 | 0.327 | +0.013 |
| Expected-context coverage | 0.560 | 0.707 | -0.147 |
| Proxy score | 0.428 | 0.479 | -0.051 |
| Average retrieved sources | 4.20 | 4.73 | -0.53 |
| Empty / cannot verify answers | 0 / 15 | 0 / 15 | 0 |

## A/B Comparison

**Config A: hybrid + rerank** gives slightly better answer keyword coverage. This means its final extractive answer sometimes contains more terms from the expected answer.

**Config B: hybrid no rerank** gives stronger expected-context coverage and a higher overall proxy score. In this run, disabling reranking preserved more evidence related to the expected source/context.

**Conclusion:** Config B is the current winner for retrieval coverage. Config A may still be useful after improving the reranker, but the current MMR step appears to remove or down-rank some legally important evidence.

## Category Breakdown

| Category | Config A proxy | Config B proxy | Better config |
|---|---:|---:|---|
| Law | 0.425 | 0.498 | Config B |
| News/context | 0.434 | 0.441 | Config B, slight |

The biggest gap is in law questions, where preserving exact legal context matters more than diversity.

## Worst Performers

### Config A: hybrid + rerank

| Rank | Case | Category | Question | Answer coverage | Context coverage | Source count | Likely failure stage |
|---:|---|---|---|---:|---:|---:|---|
| 1 | law_005 | law | Gia đình có trách nhiệm gì trong phòng, chống ma túy? | 0.045 | 0.556 | 3 | Generation selected irrelevant snippets despite partial context match |
| 2 | law_004 | law | Người sử dụng trái phép chất ma túy có phải lập hồ sơ quản lý không? | 0.211 | 0.400 | 1 | Retriever returned too little context |
| 3 | law_006 | law | Cơ sở cai nghiện ma túy bắt buộc áp dụng cho nhóm đối tượng nào? | 0.316 | 0.333 | 5 | Retrieved context too broad |
| 4 | news_005 | news | Với câu hỏi về xu hướng tội phạm ma túy gần đây, chatbot cần cảnh báo giới hạn gì? | 0.207 | 0.500 | 5 | Generation did not express the expected limitation clearly |
| 5 | law_008 | law | Hành vi chứa chấp việc sử dụng trái phép chất ma túy được hiểu như thế nào? | 0.444 | 0.250 | 5 | Missing exact legal article/context |

### Config B: hybrid no rerank

| Rank | Case | Category | Question | Answer coverage | Context coverage | Source count | Likely failure stage |
|---:|---|---|---|---:|---:|---:|---|
| 1 | law_004 | law | Người sử dụng trái phép chất ma túy có phải lập hồ sơ quản lý không? | 0.211 | 0.400 | 1 | Retriever returned too little context |
| 2 | law_008 | law | Hành vi chứa chấp việc sử dụng trái phép chất ma túy được hiểu như thế nào? | 0.333 | 0.250 | 5 | Missing exact legal article/context |
| 3 | news_004 | news | Khi có nhiều bài báo về cùng một vụ án ma túy nhưng thông tin khác nhau, chatbot nên ưu tiên nguồn nào? | 0.097 | 0.667 | 5 | Good context but weak answer synthesis |
| 4 | law_002 | law | Tội mua bán trái phép chất ma túy theo Điều 251 khác gì với tội tàng trữ trái phép chất ma túy? | 0.423 | 0.222 | 5 | Context misses comparison between Điều 249 and Điều 251 |
| 5 | news_002 | news | Nếu nguồn tin chỉ nói một người bị tạm giữ vì nghi liên quan ma túy, chatbot có nên kết luận người đó phạm tội không? | 0.192 | 0.714 | 5 | Good context but answer did not state the principle strongly enough |

## Key Findings

1. The pipeline produces answers for all 15 cases, so the end-to-end flow is working.
2. The run used `extractive_fallback`, not Gemini, so answer quality is limited by snippet extraction.
3. Config B retrieved more expected evidence than Config A, especially on legal questions.
4. Some retrieved/generated text has encoding artifacts, which hurts readability and evaluation quality.
5. Several failures are generation failures rather than pure retrieval failures: context is present, but the final answer does not synthesize it into the expected form.

## Recommendations

1. Install missing RAGAS dependencies and rerun official metrics:

```bash
pip install ragas datasets langchain-community langchain-google-genai
python group_project/evaluation/eval_pipeline.py
```

2. Enable Gemini for generation before the final demo:

```text
GEMINI_API_KEY=...
GEMINI_GENERATION_MODEL=gemini-3.1-flash-lite
RAGAS_GEMINI_MODEL=gemini-3.1-flash-lite
```

3. Use Config B as the default retrieval config for now, or tune MMR so it does not discard exact legal evidence.

4. Improve legal metadata and chunk labels, especially article numbers such as Điều 249, Điều 251, Điều 255, and Điều 256.

5. Fix source text encoding before indexing so citations and answers are readable Vietnamese instead of mojibake.

6. Add a short answer synthesis step even in fallback mode: first identify relevant law/news facts, then compose a concise answer instead of concatenating snippets.

## Deliverable Status

| Requirement | Status |
|---|---|
| `golden_dataset.json` has 15+ Q&A | Done |
| Evaluation runs over all cases | Done, raw outputs generated |
| A/B comparison has 2 configs | Done |
| Official RAGAS metrics | Blocked by missing dependency |
| Worst performer analysis | Done from raw outputs |
| Improvement recommendations | Done |
