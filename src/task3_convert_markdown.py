"""
Task 3 - Convert every file in data/landing/ to Markdown.

Legal source files are converted with Microsoft's MarkItDown as required by
the assignment. Crawled news JSON files are already markdown-like, so they are
written to .md with a small metadata header.
"""

import json
from pathlib import Path

from markitdown import MarkItDown


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _convert_legal_with_markitdown(filepath: Path) -> str:
    """Convert a legal PDF/DOC/DOCX file with MarkItDown."""
    result = MarkItDown().convert(str(filepath))
    return result.text_content


def _json_article_to_markdown(filepath: Path) -> str:
    """Convert one crawled article JSON file to markdown with metadata header."""
    data = json.loads(filepath.read_text(encoding="utf-8"))

    url = data.get("url") or data.get("source_url") or "N/A"
    crawled = data.get("date_crawled") or data.get("crawl_date") or data.get("crawled_at") or "N/A"
    title = data.get("title") or filepath.stem
    content = (
        data.get("content_markdown")
        or data.get("markdown")
        or data.get("content")
        or data.get("html")
        or ""
    )

    header = f"# {title}\n\n"
    header += f"**Source:** {url}\n"
    header += f"**Crawled:** {crawled}\n\n---\n\n"
    return header + str(content)


def convert_legal_docs():
    """Convert PDF/DOCX files in data/landing/legal/ to markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        print(f"Missing legal landing directory: {legal_dir}")
        return

    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            content = _convert_legal_with_markitdown(filepath)
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(content, encoding="utf-8")
            print(f"  Saved: {output_path}")


def convert_news_articles():
    """Convert crawled article files in data/landing/news/ to markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        print(f"Missing news landing directory: {news_dir}")
        return

    for filepath in sorted(news_dir.iterdir()):
        suffix = filepath.suffix.lower()
        output_path = output_dir / f"{filepath.stem}.md"

        if suffix == ".json":
            print(f"Converting: {filepath.name}")
            output_path.write_text(_json_article_to_markdown(filepath), encoding="utf-8")
            print(f"  Saved: {output_path}")
        elif suffix in (".html", ".md", ".txt"):
            print(f"Copying text article: {filepath.name}")
            output_path.write_text(filepath.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  Saved: {output_path}")


def convert_all():
    """Convert all supported landing files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\nDone! Output:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
