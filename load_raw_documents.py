"""Load raw documents from local files or URLs and save them in a consistent format.

This script is intended to capture raw text before any cleaning or chunking is applied.
It supports local markdown/text files and optional URL-based scraping.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_SOURCE_DIR = Path(__file__).resolve().parent / "documents" / "raw_material"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "raw_text"
SUPPORTED_EXTENSIONS = {".md", ".txt", ".html", ".htm"}


def normalize_line_endings(text: str) -> str:
    """Normalize line endings so saved raw text is consistent."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sanitize_url_path(url: str) -> str:
    """Generate a filesystem-safe path for a URL source."""
    parsed = urlparse(url)
    base = parsed.netloc + parsed.path
    base = re.sub(r"[^\w\-.]+", "_", base).strip("_")
    if not base:
        base = "url"
    return base + (".txt" if not base.endswith(".txt") else "")


def collect_local_files(root_dir: Path, extensions: set[str]) -> Iterable[Path]:
    root_dir = root_dir.resolve()
    if not root_dir.exists():
        return []
    for path in sorted(root_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions and not path.name.startswith("."):
            yield path


def load_file(path: Path) -> str:
    """Read a local text file and normalize its line endings."""
    return normalize_line_endings(path.read_text(encoding="utf-8-sig"))


def fetch_url(url: str) -> str:
    """Download text from a URL and normalize line endings."""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=15) as response:
        raw_bytes = response.read()
        text = raw_bytes.decode("utf-8", errors="replace")
        return normalize_line_endings(text)


def save_raw_text(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def create_manifest_entry(source: str, output_path: Path, source_type: str) -> dict:
    return {
        "source": source,
        "output_path": str(output_path.as_posix()),
        "source_type": source_type,
    }


def save_manifest(entries: list[dict], output_dir: Path) -> None:
    manifest_path = output_dir / "raw_manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load raw documents into a consistent raw text format.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Directory containing local source documents.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to save raw text files.")
    parser.add_argument("--urls", type=Path, help="Optional file containing one URL per line to fetch as raw text.")
    args = parser.parse_args()

    entries: list[dict] = []
    output_dir = args.output_dir.resolve()

    print(f"Loading local files from {args.source_dir}")
    for path in collect_local_files(args.source_dir, SUPPORTED_EXTENSIONS):
        raw_text = load_file(path)
        relative = path.relative_to(args.source_dir)
        save_path = output_dir / relative.with_suffix(".txt")
        save_raw_text(raw_text, save_path)
        entries.append(create_manifest_entry(str(path.relative_to(args.source_dir).as_posix()), save_path, "file"))
        print(f"Saved raw text: {save_path}")

    if args.urls:
        print(f"Fetching URLs from {args.urls}")
        if not args.urls.exists():
            raise FileNotFoundError(f"URL list file not found: {args.urls}")
        for line in args.urls.read_text(encoding="utf-8").splitlines():
            url = line.strip()
            if not url:
                continue
            try:
                raw_text = fetch_url(url)
            except (HTTPError, URLError) as exc:
                print(f"Warning: failed to fetch {url}: {exc}", file=sys.stderr)
                continue
            save_path = output_dir / sanitize_url_path(url)
            save_raw_text(raw_text, save_path)
            entries.append(create_manifest_entry(url, save_path, "url"))
            print(f"Saved raw text from URL: {url} -> {save_path}")

    if entries:
        save_manifest(entries, output_dir)
        print(f"Wrote manifest for {len(entries)} raw sources to {output_dir / 'raw_manifest.jsonl'}")
    else:
        print("No raw documents were saved.")


if __name__ == "__main__":
    main()
