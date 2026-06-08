"""Clean raw text documents by removing boilerplate, metadata, and formatting noise.

This script removes common non-substantive content like:
- Markdown metadata (frontmatter, YAML headers)
- Navigation/boilerplate sections
- Excessive whitespace
- HTML artifacts
- URL cruft and tracking pixels
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

DEFAULT_RAW_DIR = Path(__file__).resolve().parent / "data" / "raw_text"
DEFAULT_CLEAN_DIR = Path(__file__).resolve().parent / "data" / "cleaned_text"


def remove_yaml_frontmatter(text: str) -> str:
    """Remove YAML or TOML frontmatter at the start of the document."""
    # Match --- or +++ fences
    if text.startswith("---"):
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if match:
            text = text[match.end():]
    elif text.startswith("+++"):
        match = re.match(r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n", text, re.DOTALL)
        if match:
            text = text[match.end():]
    return text


def remove_html_tags(text: str) -> str:
    """Remove HTML tags but preserve text content."""
    # Remove script and style tags with their content
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove noscript tags
    text = re.sub(r"<noscript[^>]*>.*?</noscript>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove other HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    return text


def remove_navigation_and_menus(text: str) -> str:
    """Remove navigation menus, breadcrumbs, and site chrome."""
    patterns = [
        # Navigation sections
        r"(?:Navigation|Menu|Sidebar|Breadcrumb).*?(?=\n\n|$)",
        # Common nav phrases
        r"^(?:Home|Back to|Skip to|Go to).*$",
        # Skip links
        r"\[Skip to (?:main )?content\]",
        r"(?:Home|About|Contact|FAQ|Help|Search).*?\|.*?",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def remove_cookie_and_consent_banners(text: str) -> str:
    """Remove cookie notices, consent dialogs, and privacy warnings."""
    patterns = [
        r"(?:This (?:website|site) uses|Accept (?:all |)).*?cookie.*?(?:\.|$)",
        r"(?:Consent|Privacy Policy|Terms of (?:Service|Use)).*?(?=\n\n|$)",
        r"(?:We use|By (?:using|continuing)).*?(?:tracking|analytics|personalised?|cookies?).*?(?=\n\n|$)",
        r"\[Accept All\].*?\[Reject\].*?",
        r"(?:Your privacy|GDPR|Cookie (?:Settings|Management)).*?(?=\n\n|$)",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return text


def remove_ads_and_sponsorships(text: str) -> str:
    """Remove advertisement blocks, sponsored content, and promotional material."""
    patterns = [
        r"(?:Advertisement|Sponsored|Ad|Promoted Post|Featured).*?(?=\n\n|$)",
        r"\[Ad\].*?\[End Ad\]",
        r"(?:Buy Now|Shop Now|Order Today).*?(?:\.|$)",
        r"^\*?\*?(?:Advertisement|Sponsored|Promo|Special Offer)\*?\*?.*?(?:\n\n|$)",
        r"(?:Click here|Learn more|Sign up).*?(?:offer|deal|limited time).*?(?:\.|$)",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return text


def remove_footers_and_headers(text: str) -> str:
    """Remove repeated site footers, headers, and duplicated boilerplate."""
    patterns = [
        # Footer sections
        r"(?:Footer|Copyright|© \d+|All rights reserved).*?(?=\n\n|$)",
        # Repeated headers at bottom
        r"(?:Related (?:Posts?|Articles?|Content)|Further Reading|See Also|More from).*?(?=\n\n|$)",
        # Social sharing
        r"(?:Share (?:this|on)|Follow us?|Like us|Subscribe).*?(?:\(.*?\)|$)",
        # Common footer phrases
        r"^\d{4}-\d{2}-\d{2}.*?(?:\n|$)",
        r"^(?:Page \d+|Next Page|Previous Page).*?$",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def remove_markdown_metadata(text: str) -> str:
    """Remove common markdown metadata lines and comments."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        # Skip HTML comments
        if line.strip().startswith("<!--") or line.strip().startswith("-->"):
            continue
        # Skip typical metadata lines (often at start of file)
        if re.match(r"^(Author|Date|Updated|Created|Source|URL|Link):\s*", line, re.IGNORECASE):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def remove_excessive_whitespace(text: str) -> str:
    """Collapse multiple blank lines and trim trailing whitespace."""
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def remove_markdown_link_footnotes(text: str) -> str:
    """Remove markdown link reference definitions at the end."""
    # Pattern: [ref]: url or [ref]: url "title"
    text = re.sub(r"^\[.*?\]:\s*https?://[^\n]*$", "", text, flags=re.MULTILINE)
    return text


def remove_common_boilerplate(text: str) -> str:
    """Remove common navigation and boilerplate phrases."""
    boilerplate_patterns = [
        r"^(Table of Contents|Contents)\s*\n(?:[-\*]\s+.*\n)*",
        r"^(Disclaimer|Legal Notice|Copyright).*?(?=\n\n|$)",
        r"^(Last updated|Last modified|Updated on):.*$",
        r"^(Share this|Subscribe|Follow us).*$",
        r"^(Related posts|Further reading|See also):.*?(?=\n\n|$)",
        r"^\[\s*?(Advertisement|Ad|Sponsored)\s*?\].*$",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def remove_tracking_pixels_and_urls(text: str) -> str:
    """Remove tracking pixels and common analytics URLs."""
    # Remove 1x1 pixels and common tracking URLs
    text = re.sub(r"!\[.*?\]\(.*?1x1.*?\)", "", text)
    text = re.sub(r"https?://[^\s)]*?(pixel|track|analytics|ga|utm)[^\s)]*", "", text, flags=re.IGNORECASE)
    return text


def clean_text(text: str) -> str:
    """Apply all cleaning transformations."""
    text = remove_yaml_frontmatter(text)
    text = remove_html_tags(text)
    text = remove_markdown_metadata(text)
    text = remove_navigation_and_menus(text)
    text = remove_cookie_and_consent_banners(text)
    text = remove_ads_and_sponsorships(text)
    text = remove_footers_and_headers(text)
    text = remove_markdown_link_footnotes(text)
    text = remove_common_boilerplate(text)
    text = remove_tracking_pixels_and_urls(text)
    text = remove_excessive_whitespace(text)
    return text


def collect_raw_files(raw_dir: Path) -> Iterable[Path]:
    """Yield all .txt files under raw_dir, excluding manifest and hidden files."""
    raw_dir = raw_dir.resolve()
    if not raw_dir.exists():
        return []
    for path in sorted(raw_dir.rglob("*.txt")):
        if not path.name.startswith(".") and path.name != "raw_manifest.jsonl":
            yield path


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean raw text documents by removing boilerplate and noise.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Directory containing raw text files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_CLEAN_DIR, help="Directory to save cleaned text files.")
    parser.add_argument("--manifest", type=Path, help="Optional path to raw_manifest.jsonl to track cleaning.")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Cleaning documents from {args.raw_dir}")
    cleaned_count = 0
    cleaning_manifest: list[dict] = []

    for raw_path in collect_raw_files(args.raw_dir):
        raw_text = raw_path.read_text(encoding="utf-8")
        cleaned_text = clean_text(raw_text)

        relative = raw_path.relative_to(args.raw_dir)
        output_path = output_dir / relative

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cleaned_text, encoding="utf-8")

        cleaning_manifest.append({
            "input": str(raw_path.relative_to(args.raw_dir).as_posix()),
            "output": str(output_path.relative_to(output_dir).as_posix()),
            "raw_chars": len(raw_text),
            "cleaned_chars": len(cleaned_text),
            "reduction": max(0, (len(raw_text) - len(cleaned_text)) / len(raw_text) * 100) if raw_text else 0,
        })

        cleaned_count += 1
        print(f"Cleaned: {relative}")

    if cleaning_manifest:
        manifest_path = output_dir / "cleaning_manifest.jsonl"
        with manifest_path.open("w", encoding="utf-8") as fh:
            for entry in cleaning_manifest:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Cleaned {cleaned_count} documents. Manifest saved to {manifest_path}")
    else:
        print("No raw documents found to clean.")


if __name__ == "__main__":
    main()
