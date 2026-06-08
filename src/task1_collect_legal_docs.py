"""
Task 1 - Collect legal documents about drugs and prohibited substances.

The source PDFs are stored in data/landing/legal/. This module creates the
target directory and validates that the personal-task requirement is met:
at least three non-empty PDF/DOC/DOCX legal documents.
"""

from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
VALID_EXTENSIONS = {".pdf", ".docx", ".doc"}

EXPECTED_DOCUMENTS = [
    "Luat-so-732021QH15.pdf",
    "Nghi-dinh-105-2021-ND-CP-huong-dan-Luat-Phong-chong-ma-tuy-496664.pdf",
    "Luat-sua-doi-Bo-luat-Hinh-su-2017-354053.pdf",
    "Thong-tu-lien-tich-17-2015-TTLT-BYT-BLDTBXH-BCA-quy-trinh-xac-dinh-tinh-trang-nghien-ma-tuy-282421.pdf",
]


def setup_directory():
    """Create data/landing/legal/ if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def list_legal_documents() -> list[Path]:
    """Return all collected legal PDF/DOC/DOCX files."""
    setup_directory()
    return sorted(
        path
        for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS
    )


def validate_collection(min_files: int = 3) -> list[Path]:
    """Validate the legal document collection and return collected files."""
    files = list_legal_documents()
    non_empty_files = [path for path in files if path.stat().st_size > 1024]

    if len(non_empty_files) < min_files:
        names = [path.name for path in non_empty_files]
        raise RuntimeError(
            f"Need at least {min_files} non-empty legal documents; found {len(non_empty_files)}: {names}"
        )

    return non_empty_files


if __name__ == "__main__":
    collected = validate_collection()
    print(f"Collected {len(collected)} legal documents:")
    for file_path in collected:
        print(f"- {file_path.name} ({file_path.stat().st_size} bytes)")
