import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler


URLS = [
    # Thay / bổ sung URL bài báo của bạn tại đây
    "https://tuoitre.vn/ca-si-long-nhat-va-son-ngoc-minh-mua-ma-tuy-tu-dau-20260522101239371.htm",
    "https://vietnamnet.vn/ca-si-long-nhat-va-son-ngoc-minh-bi-bat-vi-ma-tuy-2399789.html",
    "https://tuoitre.vn/son-ngoc-minh-va-long-nhat-bi-bat-vi-ma-tuy-20260521141808706.htm",
    "https://vietnamnet.vn/ca-si-son-ngoc-minh-va-long-nhat-bi-bat-vi-ma-tuy-2399487.html",
    "https://tuoitre.vn/bat-ca-si-long-nhat-va-son-ngoc-minh-trong-duong-day-ma-tuy-2026052115460699.htm",
]


def slugify(text: str, max_len: int = 80) -> str:
    text = text.lower().strip()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "article"


def extract_title(markdown: str, fallback_url: str) -> str:
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.replace("# ", "", 1).strip()
    for line in markdown.splitlines():
        line = line.strip()
        if line and not line.startswith(("!", "[", "*", "-")):
            return line[:150]
    return urlparse(fallback_url).path.strip("/").split("/")[-1] or fallback_url


async def crawl_article(url: str, output_dir: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    markdown = result.markdown or ""
    title = extract_title(markdown, url)
    crawled_at = datetime.now(timezone.utc).isoformat()

    data = {
        "source_url": url,
        "crawled_at": crawled_at,
        "title": title,
        "markdown": markdown,
    }

    filename = f"{slugify(title)}.json"
    file_path = output_path / filename

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved: {file_path}")
    return file_path


async def main():
    output_dir = "data/landing/news"

    for url in URLS:
        try:
            await crawl_article(url, output_dir)
        except Exception as e:
            print(f"Failed: {url} | {e}")


if __name__ == "__main__":
    asyncio.run(main())
