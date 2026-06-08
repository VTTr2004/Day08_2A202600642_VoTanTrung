from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


EVAL_DIR = Path(__file__).resolve().parent
GROUP_PROJECT_ROOT = EVAL_DIR.parent
PROJECT_ROOT = GROUP_PROJECT_ROOT.parent
GOLDEN_DATASET_PATH = EVAL_DIR / "golden_dataset.json"
RESULTS_PATH = EVAL_DIR / "results.md"
RAW_OUTPUTS_PATH = EVAL_DIR / "raw_outputs.json"

for path in (GROUP_PROJECT_ROOT, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from group_rag.rag_adapter import RAG_CONFIGS, answer_question  # noqa: E402


METRIC_NAMES = [
    "faithfulness",
    "answer_relevancy",
    "context_recall",
    "context_precision",
]


def load_golden_dataset() -> list[dict]:
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def run_pipeline_for_config(golden_dataset: list[dict], config_name: str) -> list[dict]:
    rows = []
    for item in golden_dataset:
        result = answer_question(
            item["question"],
            history=[],
            config_name=config_name,
            top_k=5,
        )
        rows.append(
            {
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "answer": result["answer"],
                "contexts": [source["content"] for source in result["sources"]],
                "ground_truth": item["expected_answer"],
                "expected_context": item["expected_context"],
                "config": config_name,
                "model": result["model"],
                "source_count": len(result["sources"]),
            }
        )
    return rows


def _build_dataset(rows: list[dict]):
    from datasets import Dataset

    return Dataset.from_dict(
        {
            "question": [row["question"] for row in rows],
            "answer": [row["answer"] for row in rows],
            "contexts": [row["contexts"] for row in rows],
            "ground_truth": [row["ground_truth"] for row in rows],
        }
    )


def _ragas_llm_kwargs() -> dict[str, Any]:
    """Use Gemini for RAGAS when LangChain's Gemini adapter is installed."""
    try:
        import os

        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {}

        llm = ChatGoogleGenerativeAI(
            model=os.getenv("RAGAS_GEMINI_MODEL", os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.1-flash-lite")),
            google_api_key=api_key,
            temperature=0,
        )
        embeddings = GoogleGenerativeAIEmbeddings(
            model=os.getenv("RAGAS_GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"),
            google_api_key=api_key,
        )
        return {"llm": llm, "embeddings": embeddings}
    except Exception:
        return {}


def evaluate_rows_with_ragas(rows: list[dict]) -> tuple[dict, list[dict]]:
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    dataset = _build_dataset(rows)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        **_ragas_llm_kwargs(),
    )
    frame = result.to_pandas()
    records = frame.to_dict(orient="records")
    scores = {}
    for metric in METRIC_NAMES:
        values = [float(record[metric]) for record in records if record.get(metric) is not None]
        scores[metric] = mean(values) if values else None
    scores["average"] = mean([value for value in scores.values() if value is not None])
    return scores, records


def run_ab_evaluation(golden_dataset: list[dict]) -> dict:
    report = {"configs": {}, "errors": {}}
    raw_outputs = {}

    for config_name in RAG_CONFIGS:
        rows = run_pipeline_for_config(golden_dataset, config_name)
        raw_outputs[config_name] = rows
        try:
            scores, per_case_scores = evaluate_rows_with_ragas(rows)
            report["configs"][config_name] = {
                "label": RAG_CONFIGS[config_name].label,
                "scores": scores,
                "cases": per_case_scores,
            }
        except Exception as exc:
            report["errors"][config_name] = {
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            report["configs"][config_name] = {
                "label": RAG_CONFIGS[config_name].label,
                "scores": {},
                "cases": [],
            }

    RAW_OUTPUTS_PATH.write_text(json.dumps(raw_outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _format_score(value: Any) -> str:
    if value is None or value == "":
        return "n/a"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "n/a"


def _metric_table(report: dict) -> str:
    config_names = list(RAG_CONFIGS)
    lines = [
        "| Metric | "
        + " | ".join(RAG_CONFIGS[name].label for name in config_names)
        + " | Delta A-B |",
        "|---|" + "|".join("---" for _ in config_names) + "|---|",
    ]
    for metric in [*METRIC_NAMES, "average"]:
        values = [
            report["configs"].get(name, {}).get("scores", {}).get(metric)
            for name in config_names
        ]
        delta = None
        if len(values) >= 2 and values[0] is not None and values[1] is not None:
            delta = float(values[0]) - float(values[1])
        lines.append(
            f"| {metric} | "
            + " | ".join(_format_score(value) for value in values)
            + f" | {_format_score(delta)} |"
        )
    return "\n".join(lines)


def _worst_performers(report: dict) -> list[dict]:
    primary = report["configs"].get("hybrid_rerank", {})
    cases = primary.get("cases", [])
    scored = []
    for case in cases:
        values = []
        for metric in METRIC_NAMES:
            value = case.get(metric)
            if value is not None:
                values.append(float(value))
        if values:
            scored.append((mean(values), case))
    return [case for _, case in sorted(scored, key=lambda item: item[0])[:3]]


def export_results(report: dict, golden_dataset: list[dict]) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# RAG Evaluation Results",
        "",
        f"Generated: {now}",
        "",
        "## Framework",
        "",
        "RAGAS",
        "",
        "## Dataset",
        "",
        f"- Total cases: {len(golden_dataset)}",
        "- Split: 10 law cases, 5 news/context cases",
        "",
        "## Overall Scores",
        "",
        _metric_table(report),
        "",
        "## A/B Comparison",
        "",
        "- Config A: Hybrid retrieval with MMR reranking.",
        "- Config B: Hybrid retrieval without reranking.",
        "",
    ]

    if report.get("errors"):
        lines.extend(
            [
                "## Evaluation Status",
                "",
                "RAGAS did not complete for at least one config. Pipeline outputs were still saved to `raw_outputs.json`.",
                "",
            ]
        )
        for config_name, error in report["errors"].items():
            lines.extend(
                [
                    f"### {config_name}",
                    "",
                    f"Error: `{error['error']}`",
                    "",
                ]
            )

    worst = _worst_performers(report)
    lines.extend(
        [
            "## Worst Performers",
            "",
            "| # | Question | Faithfulness | Relevance | Recall | Precision |",
            "|---|---|---|---|---|---|",
        ]
    )
    if worst:
        for index, case in enumerate(worst, 1):
            question = str(case.get("question", "")).replace("|", " ")
            lines.append(
                f"| {index} | {question[:120]} | "
                f"{_format_score(case.get('faithfulness'))} | "
                f"{_format_score(case.get('answer_relevancy'))} | "
                f"{_format_score(case.get('context_recall'))} | "
                f"{_format_score(case.get('context_precision'))} |"
            )
    else:
        lines.append("| 1 | n/a - run RAGAS with required dependencies/API keys | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "1. Improve chunk metadata so citations show legal article, source title, and year more consistently.",
            "2. Add query rewriting for short follow-up questions before retrieval.",
            "3. Review bottom cases and add domain-specific synonyms for Vietnamese legal terms.",
            "",
            "## Raw Outputs",
            "",
            "`raw_outputs.json` contains generated answers and retrieved contexts for each config.",
            "",
        ]
    )
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    golden_dataset = load_golden_dataset()
    report = run_ab_evaluation(golden_dataset)
    export_results(report, golden_dataset)
    print(f"Loaded {len(golden_dataset)} cases")
    print(f"Wrote {RESULTS_PATH}")
    print(f"Wrote {RAW_OUTPUTS_PATH}")


if __name__ == "__main__":
    main()
