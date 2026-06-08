# NgÃ y 8 â€” RAG Pipeline v2

**ChÆ°Æ¡ng 2 | NgÃ y 8 trong 15**

---

## Má»¥c TiÃªu

XÃ¢y dá»±ng má»™t RAG pipeline thá»±c táº¿, end-to-end, tá»« thu tháº­p dá»¯ liá»‡u phÃ¡p luáº­t vÃ  bÃ¡o chÃ­ vá» ma tuÃ½ â†’ xá»­ lÃ½ â†’ indexing â†’ retrieval (hybrid + vectorless fallback) â†’ generation cÃ³ citation.

---

## Chá»§ Äá» Dá»¯ Liá»‡u

**PhÃ¡p luáº­t Viá»‡t Nam vá» ma tuÃ½ vÃ  cÃ¡c cháº¥t cáº¥m** + **CÃ¡c bÃ i bÃ¡o vá» nghá»‡ sÄ© liÃªn quan tá»›i ma tuÃ½**

---

## Cáº¥u TrÃºc ThÆ° Má»¥c

```
day_08_rag_pipeline_v2/
â”œâ”€â”€ README.md
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ landing/          â† Task 1 & 2: raw files (PDF, DOCX, HTML)
â”‚   â””â”€â”€ standardized/     â† Task 3: converted markdown files
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ task1_collect_legal_docs.py
â”‚   â”œâ”€â”€ task2_crawl_news.py
â”‚   â”œâ”€â”€ task3_convert_markdown.py
â”‚   â”œâ”€â”€ task4_chunking_indexing.py
â”‚   â”œâ”€â”€ task5_semantic_search.py
â”‚   â”œâ”€â”€ task6_lexical_search.py
â”‚   â”œâ”€â”€ task7_reranking.py
â”‚   â”œâ”€â”€ task8_pageindex_vectorless.py
â”‚   â”œâ”€â”€ task9_retrieval_pipeline.py
â”‚   â””â”€â”€ task10_generation.py
â”œâ”€â”€ notebooks/
â”‚   â””â”€â”€ demo.ipynb         â† Notebook demo cho buá»•i trÃ¬nh bÃ y
â”œâ”€â”€ group_project/
â”‚   â””â”€â”€ README.md          â† HÆ°á»›ng dáº«n bÃ i táº­p nhÃ³m
â”œâ”€â”€ requirements.txt
â””â”€â”€ .env.example
```

---

## Nhiá»‡m Vá»¥ Chi Tiáº¿t

### Task 1 â€” Thu Tháº­p VÄƒn Báº£n PhÃ¡p Luáº­t (CÃ¡ nhÃ¢n)

TÃ¬m vÃ  táº£i vá» **tá»‘i thiá»ƒu 3 vÄƒn báº£n phÃ¡p luáº­t** dáº¡ng PDF/DOCX vá» ma tuÃ½ vÃ  cÃ¡c cháº¥t cáº¥m. LÆ°u vÃ o `data/landing/`.

**Gá»£i Ã½ nguá»“n:**
- Luáº­t PhÃ²ng, chá»‘ng ma tuÃ½ 2021 (Luáº­t sá»‘ 73/2021/QH15)
- Nghá»‹ Ä‘á»‹nh 105/2021/NÄ-CP hÆ°á»›ng dáº«n thi hÃ nh Luáº­t PhÃ²ng chá»‘ng ma tuÃ½
- Bá»™ luáº­t HÃ¬nh sá»± 2015 (sá»­a Ä‘á»•i 2017) â€” ChÆ°Æ¡ng XX: CÃ¡c tá»™i pháº¡m vá» ma tuÃ½
- ThÃ´ng tÆ° liÃªn tá»‹ch vá» danh má»¥c cháº¥t ma tuÃ½ vÃ  tiá»n cháº¥t

**YÃªu cáº§u:**
- LÆ°u file gá»‘c (PDF/DOCX) vÃ o `data/landing/legal/`
- Äáº·t tÃªn file rÃµ rÃ ng: `luat-phong-chong-ma-tuy-2021.pdf`, `nghi-dinh-105-2021.pdf`, ...

---

### Task 2 â€” Crawl BÃ i BÃ¡o (CÃ¡ nhÃ¢n)

Crawl **tá»‘i thiá»ƒu 5 bÃ i bÃ¡o** vá» cÃ¡c nghá»‡ sÄ© Viá»‡t Nam liÃªn quan tá»›i ma tuÃ½.

**ThÆ° viá»‡n khuyáº¿n nghá»‹:** [Crawl4AI](https://github.com/unclecode/crawl4ai)

**YÃªu cáº§u:**
- LÆ°u output vÃ o `data/landing/news/`
- Má»—i bÃ i bÃ¡o lÆ°u thÃ nh 1 file (JSON hoáº·c HTML)
- Ghi rÃµ metadata: URL gá»‘c, ngÃ y crawl, tiÃªu Ä‘á» bÃ i bÃ¡o

**Code máº«u (Crawl4AI):**
```python
from crawl4ai import AsyncWebCrawler

async def crawl_article(url: str, output_dir: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        # LÆ°u result.markdown vÃ o file
        ...
```

---

### Task 3 â€” Convert Sang Markdown (CÃ¡ nhÃ¢n)

Sá»­ dá»¥ng [MarkItDown](https://github.com/microsoft/markitdown) cá»§a Microsoft Ä‘á»ƒ convert toÃ n bá»™ file trong `data/landing/` thÃ nh Markdown.

**CÃ i Ä‘áº·t:**
```bash
pip install markitdown
```

**Code máº«u:**
```python
from markitdown import MarkItDown

md = MarkItDown()

# Convert PDF
result = md.convert("data/landing/legal/luat-phong-chong-ma-tuy-2021.pdf")
print(result.text_content)

# Convert DOCX
result = md.convert("data/landing/legal/nghi-dinh-105-2021.docx")
```

**YÃªu cáº§u:**
- Output lÆ°u vÃ o `data/standardized/`
- Giá»¯ nguyÃªn cáº¥u trÃºc thÆ° má»¥c con (`legal/`, `news/`)
- Má»—i file output cÃ³ tÃªn tÆ°Æ¡ng á»©ng: `luat-phong-chong-ma-tuy-2021.md`

---

### Task 4 â€” Chunking & Indexing (CÃ¡ nhÃ¢n)

Chá»n **má»™t loáº¡i chunking strategy** vÃ  **má»™t embedding model** Ä‘á»ƒ index toÃ n bá»™ markdown files vÃ o vector store.

**Chunking â€” khuyáº¿n khÃ­ch dÃ¹ng [langchain-text-splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/):**
```bash
pip install langchain-text-splitters
```

CÃ¡c loáº¡i splitter phÃ¹ há»£p:
- `RecursiveCharacterTextSplitter` (máº·c Ä‘á»‹nh, an toÃ n)
- `MarkdownHeaderTextSplitter` (tá»‘t cho file cÃ³ heading rÃµ)
- `SemanticChunker` (nÃ¢ng cao, dÃ¹ng embedding Ä‘á»ƒ tÃ¡ch)

**Embedding model gá»£i Ã½:**
- `sentence-transformers/all-MiniLM-L6-v2` (nháº¹, nhanh)
- `BAAI/bge-m3` (multilingual, tá»‘t cho tiáº¿ng Viá»‡t)
- OpenAI `text-embedding-3-small` (náº¿u cÃ³ API key)

**Vector Store - dung ChromaDB local:**
```bash
pip install chromadb
```
- ChromaDB chay local, khong can Docker hoac cloud service
- Persistent index nam trong `data/index/chroma`
- Alternatives: Weaviate (hybrid search built-in), FAISS (neu chi can dense)

**YÃªu cáº§u:**
- Ghi rÃµ trong code: dÃ¹ng chunking nÃ o, chunk_size bao nhiÃªu, overlap bao nhiÃªu, vÃ¬ sao
- Ghi rÃµ embedding model nÃ o, dimension bao nhiÃªu
- Index thÃ nh cÃ´ng toÃ n bá»™ documents

---

### Task 5 â€” Semantic Search Module (CÃ¡ nhÃ¢n)

Viáº¿t module thá»±c hiá»‡n **semantic search** (dense retrieval) trÃªn vector store.

**YÃªu cáº§u:**
```python
def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    ...
```

- Input: query string + top_k
- Output: danh sÃ¡ch chunks cÃ³ score, sorted descending
- Pháº£i hoáº¡t Ä‘á»™ng Ä‘Æ°á»£c vá»›i embedding model Ä‘Ã£ chá»n á»Ÿ Task 4

---

### Task 6 â€” Lexical Search Module (CÃ¡ nhÃ¢n)

Viáº¿t module thá»±c hiá»‡n **lexical search**. Máº·c Ä‘á»‹nh sá»­ dá»¥ng **BM25**.

```bash
pip install rank-bm25
```

**Code máº«u BM25:**
```python
from rank_bm25 import BM25Okapi

# Tokenize corpus
tokenized_corpus = [doc.split() for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

# Search
tokenized_query = query.split()
scores = bm25.get_scores(tokenized_query)
```

**YÃªu cáº§u:**
```python
def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    ...
```

**Bonus:** Náº¿u dÃ¹ng phÆ°Æ¡ng phÃ¡p khÃ¡c (TF-IDF, Elasticsearch, Weaviate BM25 built-in), hÃ£y giáº£i thÃ­ch cÆ¡ cháº¿ hoáº¡t Ä‘á»™ng trong buá»•i demo â†’ **+5 Ä‘iá»ƒm bonus**.

---

### Task 7 â€” Reranking Module (CÃ¡ nhÃ¢n)

Viáº¿t module **reranking** Ä‘á»ƒ cháº¥m láº¡i Ä‘á»™ liÃªn quan cá»§a káº¿t quáº£ retrieval.

**Lá»±a chá»n (chá»n 1):**

| PhÆ°Æ¡ng phÃ¡p | ThÆ° viá»‡n / Model | Äáº·c Ä‘iá»ƒm |
|-------------|-----------------|-----------|
| Cross-encoder reranker | `jinaai/jina-reranker-v2-base-multilingual` | Multilingual, tá»‘t cho tiáº¿ng Viá»‡t |
| Cross-encoder reranker | `Qwen/Qwen3-Reranker-0.6B` | Nháº¹, hiá»‡u quáº£ |
| MMR (Maximal Marginal Relevance) | Tá»± implement | Giáº£m trÃ¹ng láº·p, tÄƒng diversity |
| RRF (Reciprocal Rank Fusion) | Tá»± implement | Gá»™p káº¿t quáº£ tá»« nhiá»u ranker |

**Code máº«u (Jina Reranker via API):**
```python
import requests

def rerank(query: str, documents: list[str], top_k: int = 5) -> list[dict]:
    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents,
            "top_n": top_k
        }
    )
    return response.json()["results"]
```

**YÃªu cáº§u:**
```python
def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score and re-order candidates based on relevance to query.
    """
    ...
```

---

### Task 8 â€” PageIndex Vectorless RAG (CÃ¡ nhÃ¢n)

ÄÄƒng kÃ½ tÃ i khoáº£n táº¡i [https://pageindex.ai/](https://pageindex.ai/), sau Ä‘Ã³ sá»­ dá»¥ng [PageIndex SDK](https://github.com/VectifyAI/PageIndex) Ä‘á»ƒ táº¡o má»™t **vectorless RAG pipeline**.

**CÃ i Ä‘áº·t:**
```bash
pip install pageindex
```

**Tham kháº£o:** [https://github.com/VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex)

**YÃªu cáº§u:**
- Upload tÃ i liá»‡u lÃªn PageIndex
- Viáº¿t function query PageIndex vÃ  tráº£ vá» káº¿t quáº£
```python
def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using PageIndex.
    Fallback khi hybrid search khÃ´ng tráº£ vá» káº¿t quáº£ phÃ¹ há»£p.
    """
    ...
```

---

### Task 9 â€” Retrieval Pipeline HoÃ n Chá»‰nh (CÃ¡ nhÃ¢n)

Káº¿t há»£p táº¥t cáº£ modules thÃ nh má»™t **retrieval pipeline** thá»‘ng nháº¥t vá»›i logic fallback:

```
Query
  â”‚
  â”œâ”€â†’ Semantic Search (Task 5)  â”€â”€â”
  â”‚                                â”œâ”€â†’ Merge + Rerank (Task 7) â†’ Results
  â”œâ”€â†’ Lexical Search (Task 6)  â”€â”€â”˜
  â”‚
  â””â”€â†’ Náº¿u hybrid search khÃ´ng cÃ³ káº¿t quáº£ Ä‘á»§ tá»‘t (score < threshold)
        â””â”€â†’ Fallback: PageIndex Vectorless (Task 8)
```

**YÃªu cáº§u:**
```python
def retrieve(query: str, top_k: int = 5, score_threshold: float = 0.3) -> list[dict]:
    """
    1. Cháº¡y semantic_search + lexical_search
    2. Merge káº¿t quáº£ (RRF hoáº·c weighted fusion)
    3. Rerank
    4. Náº¿u top result score < threshold â†’ fallback PageIndex
    5. Return top_k results
    """
    ...
```

---

### Task 10 â€” Generation CÃ³ Citation (CÃ¡ nhÃ¢n)

Sáº¯p xáº¿p láº¡i context chunks sau reranking Ä‘á»ƒ **trÃ¡nh lost in the middle**, inject vÃ o prompt, vÃ  yÃªu cáº§u LLM tráº£ lá»i cÃ³ **citation**.

**Document Reordering (trÃ¡nh lost in the middle):**
```python
def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sáº¯p xáº¿p chunks theo pattern: quan trá»ng nháº¥t á»Ÿ Ä‘áº§u vÃ  cuá»‘i,
    Ã­t quan trá»ng hÆ¡n á»Ÿ giá»¯a.
    VÃ­ dá»¥: [1, 3, 5, 4, 2] thay vÃ¬ [1, 2, 3, 4, 5]
    """
    ...
```

**Prompt template:**
```python
SYSTEM_PROMPT = """Answer the following question comprehensively.
For every statement of fact or claim, immediately insert a citation
in brackets linking to the specific source
(e.g., [Author/Platform Name, Year]).
If the information is not explicitly stated in the provided context
or knowledge base, state 'I cannot verify this information'
rather than guessing."""

def generate_with_citation(query: str, context_chunks: list[dict]) -> str:
    """
    1. Reorder chunks Ä‘á»ƒ trÃ¡nh lost in the middle
    2. Format context vá»›i source metadata
    3. Inject vÃ o prompt vá»›i SYSTEM_PROMPT
    4. Gá»i LLM (OpenAI, Gemini, hoáº·c local model)
    5. Return answer cÃ³ citation
    """
    ...
```

**YÃªu cáº§u:**
- Chá»n top_k vÃ  top_p phÃ¹ há»£p (giáº£i thÃ­ch lÃ½ do trong code comment)
- Output pháº£i cÃ³ citation dáº¡ng `[Nguá»“n, NÄƒm]`
- Náº¿u khÃ´ng Ä‘á»§ evidence â†’ tráº£ vá» "I cannot verify this information"

---

## BÃ i Táº­p NhÃ³m

> **Sau khi hoÃ n thÃ nh bÃ i cÃ¡ nhÃ¢n**, ngá»“i láº¡i vá»›i nhÃ³m Ä‘á»ƒ xÃ¢y dá»±ng **1 trong 2 sáº£n pháº©m** sau:

---

### YÃªu cáº§u 1: Sáº£n pháº©m nhÃ³m RAG Chatbot

XÃ¢y dá»±ng chatbot tráº£ lá»i cÃ¢u há»i vá» phÃ¡p luáº­t ma tuÃ½ vÃ  tin tá»©c liÃªn quan.

**YÃªu cáº§u:**
- Giao diá»‡n chat (Streamlit / Gradio / Chainlit)
- Tráº£ lá»i cÃ³ citation (dá»±a trÃªn Task 10)
- Há»— trá»£ follow-up questions (conversation memory)
- Hiá»ƒn thá»‹ source documents Ä‘Ã£ dÃ¹ng

**Stack gá»£i Ã½:**
```
Chainlit/Streamlit â†’ Retrieval (Task 9) â†’ Generation (Task 10) â†’ Display
```

---

### YÃªu cáº§u 2: RAG Evaluation Pipeline

Sá»­ dá»¥ng **1 trong 3 framework** sau Ä‘á»ƒ evaluate pipeline RAG cá»§a nhÃ³m:

#### Framework lá»±a chá»n

| Framework | CÃ i Ä‘áº·t | Äáº·c Ä‘iá»ƒm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiá»u metric built-in, dá»… integrate vá»›i pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuáº©n industry cho RAG eval, 3 trá»¥c chÃ­nh |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions máº¡nh |

#### YÃªu cáº§u Evaluation

1. **Táº¡o Golden Dataset** â€” tá»‘i thiá»ƒu 15 cáº·p Q&A (question, expected_answer, expected_context)
2. **Cháº¡y evaluation** trÃªn toÃ n bá»™ golden dataset vá»›i cÃ¡c metrics sau:
   - **Faithfulness** â€” cÃ¢u tráº£ lá»i cÃ³ bÃ¡m Ä‘Ãºng context khÃ´ng?
   - **Answer Relevance** â€” cÃ¢u tráº£ lá»i cÃ³ Ä‘Ãºng cÃ¢u há»i khÃ´ng?
   - **Context Recall** â€” retriever cÃ³ láº¥y Ä‘á»§ evidence khÃ´ng?
   - **Context Precision** â€” trong context láº¥y vá», bao nhiÃªu % thá»±c sá»± há»¯u Ã­ch?
3. **So sÃ¡nh A/B** â€” cháº¡y eval trÃªn Ã­t nháº¥t 2 config khÃ¡c nhau (vÃ­ dá»¥: cÃ³ reranking vs khÃ´ng reranking, hoáº·c hybrid vs dense-only)
4. **BÃ¡o cÃ¡o** â€” báº£ng Ä‘iá»ƒm + phÃ¢n tÃ­ch worst performers + Ä‘á» xuáº¥t cáº£i tiáº¿n

#### Code máº«u â€” DeepEval

```python
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
from deepeval.test_case import LLMTestCase

# Táº¡o test cases tá»« golden dataset
test_cases = []
for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    test_case = LLMTestCase(
        input=item["question"],
        actual_output=result["answer"],
        expected_output=item["expected_answer"],
        retrieval_context=[c["content"] for c in result["sources"]],
    )
    test_cases.append(test_case)

# Cháº¡y evaluation
metrics = [
    FaithfulnessMetric(threshold=0.7),
    AnswerRelevancyMetric(threshold=0.7),
    ContextualRecallMetric(threshold=0.7),
    ContextualPrecisionMetric(threshold=0.7),
]

results = evaluate(test_cases, metrics)
```

#### Code máº«u â€” RAGAS

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset

# Chuáº©n bá»‹ data
eval_data = {
    "question": [],
    "answer": [],
    "contexts": [],
    "ground_truth": [],
}

for item in golden_dataset:
    result = rag_pipeline.generate_with_citation(item["question"])
    eval_data["question"].append(item["question"])
    eval_data["answer"].append(result["answer"])
    eval_data["contexts"].append([c["content"] for c in result["sources"]])
    eval_data["ground_truth"].append(item["expected_answer"])

dataset = Dataset.from_dict(eval_data)

# Cháº¡y evaluation
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
)
print(result.to_pandas())
```

#### Code máº«u â€” TruLens

```python
from trulens.apps.custom import TruCustomApp, instrument
from trulens.core import Feedback
from trulens.providers.openai import OpenAI as TruOpenAI

provider = TruOpenAI()

# Define feedback functions
f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
f_relevance = Feedback(provider.relevance).on_input_output()
f_context_relevance = Feedback(provider.context_relevance).on_input()

# Wrap RAG pipeline
tru_rag = TruCustomApp(
    rag_pipeline,
    app_name="DrugLaw_RAG",
    feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
)

# Run evaluation
with tru_rag as recording:
    for item in golden_dataset:
        rag_pipeline.generate_with_citation(item["question"])

# View dashboard
from trulens.dashboard import run_dashboard
run_dashboard()
```

#### Deliverable Evaluation

- [ ] File `group_project/evaluation/golden_dataset.json` â€” 15+ cáº·p Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` â€” script cháº¡y evaluation
- [ ] File `group_project/evaluation/results.md` â€” báº£ng Ä‘iá»ƒm + phÃ¢n tÃ­ch
- [ ] So sÃ¡nh A/B Ã­t nháº¥t 2 configs

---

### YÃªu Cáº§u Chung

1. **TÃ­ch há»£p pipeline** tá»« bÃ i cÃ¡ nhÃ¢n cá»§a cÃ¡c thÃ nh viÃªn
2. **Demo hoáº¡t Ä‘á»™ng Ä‘Æ°á»£c** trong buá»•i trÃ¬nh bÃ y (cháº¡y local hoáº·c deploy)
3. **Evaluation pipeline** cháº¡y Ä‘Æ°á»£c vÃ  cÃ³ bÃ¡o cÃ¡o káº¿t quáº£
4. **Code push lÃªn repository** chung cá»§a nhÃ³m
5. **README** mÃ´ táº£ kiáº¿n trÃºc vÃ  phÃ¢n cÃ´ng (xem `group_project/README.md`)

---

### Kiáº¿n TrÃºc Há»‡ Thá»‘ng

```
[Váº½ diagram kiáº¿n trÃºc á»Ÿ Ä‘Ã¢y]
```

---

### PhÃ¢n CÃ´ng CÃ´ng Viá»‡c

| ThÃ nh viÃªn | MSSV | Nhiá»‡m vá»¥ | Tráº¡ng thÃ¡i |
|-----------|------|----------|------------|
| | | | |
| | | | |
| | | | |
| | | | |

---

### HÆ°á»›ng Dáº«n Cháº¡y

```bash
# CÃ i Ä‘áº·t dependencies
pip install -r requirements.txt

# Cháº¡y app
streamlit run app.py
# hoáº·c
chainlit run app.py
```

---

### LÆ°u Ã½

HÃ£y giá»¯ láº¡i repo nÃ y náº¿u nhÆ° báº¡n há»c track 3 giai Ä‘oáº¡n 2, chÃºng ta sáº½ phÃ¡t triá»ƒn tiáº¿p dá»± Ã¡n lÃªn knowledge graph Ä‘á»ƒ kháº¯c phá»¥c cÃ¡c cÃ¢u há»i hÃ³c bÃºa khi cÃ³ cÃ¡c cÃ¢u há»i khÃ³.

---

## CÃ i Äáº·t MÃ´i TrÆ°á»ng

```bash
pip install -r requirements.txt
```

Táº¡o file `.env` tá»« `.env.example`:
```bash
cp .env.example .env
# Äiá»n API keys vÃ o .env
```

---

## Cháº¥m Äiá»ƒm

### Tá»•ng Quan PhÃ¢n Bá»• Äiá»ƒm

| ThÃ nh pháº§n | Tá»· trá»ng | MÃ´ táº£ |
|-----------|----------|-------|
| **BÃ i CÃ¡ NhÃ¢n** | **50%** | 10 tasks, cháº¥m báº±ng automated tests + manual review |
| **BÃ i NhÃ³m** | **30%** | RAG Chatbot + Evaluation pipeline |
| **Bonus** | **20%** | CÃ¡c tiÃªu chÃ­ nÃ¢ng cao (xem bÃªn dÆ°á»›i) |

---

### BÃ i CÃ¡ NhÃ¢n â€” 50 Ä‘iá»ƒm (50%)

Cháº¥m báº±ng automated test suite (`pytest tests/ -v`). Má»—i task cÃ³ test riÃªng.

| Task | Ná»™i dung | Äiá»ƒm | Test |
|------|----------|------|------|
| 1 | Thu tháº­p vÄƒn báº£n phÃ¡p luáº­t (â‰¥3 files tá»“n táº¡i trong `data/landing/legal/`) | 3 | `test_task1_*` |
| 2 | Crawl bÃ i bÃ¡o (â‰¥5 files tá»“n táº¡i trong `data/landing/news/`) | 3 | `test_task2_*` |
| 3 | Convert markdown (files tá»“n táº¡i trong `data/standardized/`) | 4 | `test_task3_*` |
| 4 | Chunking + Indexing (vector store cÃ³ data) | 7 | `test_task4_*` |
| 5 | Semantic search tráº£ vá» káº¿t quáº£ Ä‘Ãºng format, sorted | 6 | `test_task5_*` |
| 6 | Lexical search (BM25) tráº£ vá» káº¿t quáº£ Ä‘Ãºng format | 6 | `test_task6_*` |
| 7 | Reranking hoáº¡t Ä‘á»™ng, output re-sorted | 6 | `test_task7_*` |
| 8 | PageIndex query tráº£ vá» káº¿t quáº£ | 4 | `test_task8_*` |
| 9 | Retrieval pipeline + fallback logic hoáº¡t Ä‘á»™ng | 7 | `test_task9_*` |
| 10 | Generation cÃ³ citation + reorder | 4 | `test_task10_*` |
| **Tá»•ng** | | **50** | |

---

### BÃ i NhÃ³m â€” 30 Ä‘iá»ƒm (30%)

| TiÃªu chÃ­ | Äiá»ƒm |
|----------|------|
| RAG Chatbot demo hoáº¡t Ä‘á»™ng Ä‘Æ°á»£c | 8 |
| TÃ­ch há»£p pipeline cÃ¡c thÃ nh viÃªn | 4 |
| Kiáº¿n trÃºc rÃµ rÃ ng + README | 3 |
| Cháº¥t lÆ°á»£ng cÃ¢u tráº£ lá»i (cÃ³ citation, Ä‘Ãºng ná»™i dung) | 3 |
| **Evaluation pipeline** (DeepEval / RAGAS / TruLens) | **12** |
| â€” Golden dataset â‰¥15 Q&A pairs | 3 |
| â€” Cháº¡y eval vá»›i â‰¥4 metrics | 4 |
| â€” So sÃ¡nh A/B â‰¥2 configs + phÃ¢n tÃ­ch | 3 |
| â€” BÃ¡o cÃ¡o káº¿t quáº£ cÃ³ phÃ¢n tÃ­ch worst performers | 2 |

---

### Bonus â€” 20 Ä‘iá»ƒm (20%)

Demo hoáº·c Ä‘áº·t cÃ¢u há»i mÃ  nhÃ³m Ä‘ang demo khiáº¿n LLM khÃ´ng tráº£ lá»i Ä‘Æ°á»£c (má»—i cÃ¢u 5 Ä‘iá»ƒm)

---

### Cháº¡y Test Cháº¥m Äiá»ƒm BÃ i CÃ¡ NhÃ¢n

```bash
# Cháº¡y toÃ n bá»™ test suite
pytest tests/ -v

# Cháº¡y tá»«ng task
pytest tests/test_individual.py::TestTask1 -v
pytest tests/test_individual.py::TestTask5 -v
```

---

## HÆ°á»›ng Dáº«n Thá»i Gian

| Giai Ä‘oáº¡n | Thá»i gian | Hoáº¡t Ä‘á»™ng |
|-----------|-----------|-----------|
| Task 1â€“3 | 0:00â€“0:45 | Thu tháº­p data + convert markdown |
| Task 4â€“6 | 0:45â€“1:45 | Chunking, indexing, search modules |
| Task 7â€“8 | 1:45â€“2:15 | Reranking + PageIndex setup |
| Task 9â€“10 | 2:15â€“3:00 | Pipeline hoÃ n chá»‰nh + generation |
| BÃ i nhÃ³m | NgoÃ i giá» | TÃ­ch há»£p + build demo |

---

## TÃ i Liá»‡u Tham Kháº£o

- [Crawl4AI](https://github.com/unclecode/crawl4ai) â€” Web crawling library
- [MarkItDown](https://github.com/microsoft/markitdown) â€” Microsoft document converter
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/) â€” Chunking strategies
- [Weaviate](https://weaviate.io/developers/weaviate) â€” Vector database with hybrid search
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) â€” BM25 implementation
- [PageIndex](https://github.com/VectifyAI/PageIndex) â€” Vectorless RAG
- [Jina Reranker](https://jina.ai/reranker/) â€” Cross-encoder reranking API
- Liu et al. (2023), *Lost in the Middle: How Language Models Use Long Contexts*
# Day08_RAG_pipeline_cohort2
