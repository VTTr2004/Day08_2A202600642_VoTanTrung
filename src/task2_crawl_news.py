"""
Task 2 - Crawl news articles about Vietnamese artists related to drugs.

The preferred crawler is Crawl4AI. A lightweight requests-based fallback is
included so the script can still run in environments where Crawl4AI is not
installed yet.
"""

import asyncio
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://tuoitre.vn/ca-si-long-nhat-va-son-ngoc-minh-mua-ma-tuy-tu-dau-20260522101239371.htm",
    "https://vietnamnet.vn/tp-hcm-khoi-to-71-doi-tuong-trong-duong-day-ma-tuy-lon-co-ca-si-long-nhat-2517560.html",
    "https://vietnamnet.vn/nsut-hanh-thuy-noi-gi-sau-khi-ca-si-long-nhat-va-son-ngoc-minh-bi-bat-vi-ma-tuy-2517587.html",
    "https://vietnamnet.vn/su-nghiep-on-ao-cua-ca-si-long-nhat-truoc-khi-sup-do-vi-vuong-vao-ma-tuy-2517570.html",
    "https://vietnamnet.vn/tu-vu-ca-si-long-nhat-son-ngoc-minh-bi-bat-tam-giam-can-phong-sat-2517641.html",
]


def setup_directory():
    """Create data/landing/news/ when needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def slugify(text: str, max_len: int = 90) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "article"


def extract_title(markdown: str, fallback_url: str) -> str:
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return urlparse(fallback_url).path.rsplit("/", 1)[-1] or fallback_url


def html_to_markdown(raw_html: str, url: str) -> str:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, flags=re.I | re.S)
    title = html.unescape(title_match.group(1)).strip() if title_match else extract_title("", url)
    title = re.sub(r"\s+", " ", title)

    body = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw_html, flags=re.I | re.S)
    body = re.sub(r"</(p|h1|h2|h3|li|div|br)>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    lines = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines()]
    lines = [line for line in lines if len(line) > 40]
    content = "\n\n".join(lines[:80])
    return f"# {title}\n\n{content}"


async def crawl_article(url: str) -> dict:
    """
    Crawl one article and return metadata plus markdown content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str,
            "content_markdown": str
        }
    """
    try:
        from crawl4ai import AsyncWebCrawler

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
        markdown = result.markdown or ""
        title = result.metadata.get("title") or extract_title(markdown, url)
    except ImportError:
        import requests

        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Day08RAG/1.0)"},
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        markdown = html_to_markdown(response.text, url)
        title = extract_title(markdown, url)

    crawled_at = datetime.now(timezone.utc).isoformat()
    return {
        "url": url,
        "source_url": url,
        "title": title,
        "date_crawled": crawled_at,
        "crawl_date": crawled_at,
        "content_markdown": markdown,
        "markdown": markdown,
    }


async def crawl_all():
    """Crawl every URL in ARTICLE_URLS into data/landing/news/."""
    setup_directory()

    saved_files = []
    for index, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)
        filename = f"{index:02d}-{slugify(article['title'])}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        saved_files.append(filepath)
        print(f"  Saved: {filepath}")
    return saved_files


if __name__ == "__main__":
    asyncio.run(crawl_all())
