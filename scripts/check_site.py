#!/usr/bin/env python3
"""Fail closed unless the complete public repository matches its reviewed projection."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit


DEFAULT_ROOT = Path(__file__).resolve().parent.parent
BASE_PATH = "/infamous/"
AUTOMATION_NAME = "BucketComps Automation"
AUTOMATION_EMAIL = "bucketcomps-automation@users.noreply.github.com"

EXPECTED_REPOSITORY_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/workflows/pages.yml",
    ".gitignore",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "docs/ARCHITECTURE.md",
    "docs/PUBLISHING.md",
    "docs/SANITIZED-SNAPSHOT.md",
    "docs/SECURITY-BOUNDARY.md",
    "scripts/check_site.py",
    "site/404.html",
    "site/assets/site.css",
    "site/data/status.json",
    "site/devlog/index.html",
    "site/index.html",
    "site/method/index.html",
    "site/roadmap/index.html",
    "tests/test_check_site.py",
}
EXPECTED_SITE_FILES = {
    "404.html",
    "assets/site.css",
    "data/status.json",
    "devlog/index.html",
    "index.html",
    "method/index.html",
    "roadmap/index.html",
}
EXPECTED_ACTIONS = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d",
    "actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9",
    "actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128",
)
EXPECTED_STATUS = {
    "schema_version": 1,
    "as_of": "2026-07-23",
    "renderer": {
        "steps_done": 4,
        "steps_total": 13,
        "draws": 0,
        "flips": 0,
        "captures": 0,
        "verified_frames": 0,
    },
    "lifted_fallback": {
        "functions": 20298,
        "inventory_total": 20298,
        "clean_source_proof": False,
    },
    "save_system": {
        "checks_represented": 4,
        "checks_total": 34,
        "end_to_end_gameplay_cycle": False,
    },
    "texture_decode": {
        "percent": 98.1,
        "records": 15437,
    },
    "model": {
        "name": "ArcEndian Fast",
        "verified_pass": 18,
        "verified_total": 75,
        "accuracy_percent": 24.0,
        "accepted_into_source": 0,
    },
    "finish_line": "verified playable gameplay with working save and load",
}
FORBIDDEN_SUFFIXES = {
    ".3ds",
    ".avi",
    ".bin",
    ".dds",
    ".elf",
    ".iso",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".png",
    ".psarc",
    ".self",
    ".sprx",
    ".wav",
}
FORBIDDEN_FRAGMENTS = (
    "/" + "var" + "/" + "home" + "/",
    "/" + "home" + "/",
    "infamous" + "-decomp",
    "proof" + "_scope",
    "BEGIN" + " PRIVATE KEY",
    "CF_" + "API_TOKEN",
    "GITHUB_" + "TOKEN",
    "gmail" + ".com",
    "jerry" + "mares",
    "Jerry" + " Mares",
)
SECRET_PATTERNS = (
    re.compile(r"gh[opsu]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
)
EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.h1 = 0
        self.lang = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html" and values.get("lang"):
            self.lang = True
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "h1":
            self.h1 += 1
        if tag in {"a", "link", "script"}:
            attr = "href" if tag in {"a", "link"} else "src"
            if values.get(attr):
                self.links.append((tag, values[attr] or ""))


def fail(message: str) -> None:
    raise AssertionError(message)


def public_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            fail(f"symlink forbidden in public repository: {relative.as_posix()}")
        if path.is_file():
            result.append(path)
    return sorted(result)


def check_inventory(root: Path, files: list[Path]) -> None:
    actual = {path.relative_to(root).as_posix() for path in files}
    missing = sorted(EXPECTED_REPOSITORY_FILES - actual)
    extra = sorted(actual - EXPECTED_REPOSITORY_FILES)
    if missing or extra:
        fail(f"repository inventory mismatch; missing={missing}, extra={extra}")

    site = root / "site"
    actual_site = {
        path.relative_to(site).as_posix()
        for path in files
        if path.is_relative_to(site)
    }
    missing_site = sorted(EXPECTED_SITE_FILES - actual_site)
    extra_site = sorted(actual_site - EXPECTED_SITE_FILES)
    if missing_site or extra_site:
        fail(f"published inventory mismatch; missing={missing_site}, extra={extra_site}")

    if any(path.suffix.lower() in FORBIDDEN_SUFFIXES for path in files):
        fail("game/media-like file forbidden in public repository")


def check_disclosures(root: Path, files: list[Path]) -> None:
    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError as error:
            raise AssertionError(
                f"non-UTF-8 file forbidden in public repository: {relative}"
            ) from error
        for fragment in FORBIDDEN_FRAGMENTS:
            if fragment.lower() in text.lower():
                fail(f"forbidden disclosure marker in {relative}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"secret-like token in {relative}")
        for email in EMAIL_PATTERN.findall(text):
            if email.lower() != AUTOMATION_EMAIL:
                fail(f"non-automation email address in {relative}")


def local_target(site: Path, source: Path, link: str) -> Path:
    parsed = urlsplit(link)
    path = parsed.path
    if path.startswith(BASE_PATH):
        return site / path.removeprefix(BASE_PATH)
    if path.startswith("/"):
        fail(f"absolute local link escapes {BASE_PATH}: {link}")
    return source if not path else source.parent / path


def check_documents(root: Path) -> dict[Path, Document]:
    site = root / "site"
    documents: dict[Path, Document] = {}
    for path in sorted(site.rglob("*.html")):
        document = Document()
        document.feed(path.read_text(encoding="utf-8"))
        documents[path.resolve()] = document
        if document.h1 != 1 or not document.lang:
            fail(f"{path.relative_to(site)} needs one h1 and an html language")
        if "#main" not in [value for tag, value in document.links if tag == "a"]:
            fail(f"{path.relative_to(site)} is missing a skip link")

    for source, document in documents.items():
        for _tag, link in document.links:
            parsed = urlsplit(link)
            if parsed.scheme:
                if parsed.scheme != "https":
                    fail(f"non-HTTPS link in {source.relative_to(site)}: {link}")
                continue
            if link.startswith("//"):
                fail(f"scheme-relative link forbidden: {link}")
            target = local_target(site, source, link)
            if target.is_dir():
                target /= "index.html"
            if not target.exists():
                fail(f"broken local link in {source.relative_to(site)}: {link}")
            if parsed.fragment and target.suffix == ".html":
                target_document = documents.get(target.resolve())
                if target_document is None:
                    target_document = Document()
                    target_document.feed(target.read_text(encoding="utf-8"))
                if parsed.fragment not in target_document.ids:
                    fail(f"missing fragment in {source.relative_to(site)}: {link}")

    not_found = (site / "404.html").read_text(encoding="utf-8")
    required_404_links = (
        'href="/infamous/assets/site.css"',
        'href="/infamous/"',
    )
    if any(marker not in not_found for marker in required_404_links):
        fail(f"404 document must preserve the {BASE_PATH} project base")

    architecture = (root / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    architecture_paths = (
        "`/infamous/`",
        "`/infamous/devlog/`",
        "`/infamous/method/`",
        "`/infamous/roadmap/`",
        "`/infamous/data/status.json`",
    )
    if any(path not in architecture for path in architecture_paths):
        fail(f"architecture content map must use the {BASE_PATH} project base")
    return documents


def channel(value: int) -> float:
    component = value / 255
    return component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4


def contrast_ratio(foreground: str, background: str) -> float:
    colors = []
    for value in (foreground, background):
        red, green, blue = (int(value[index:index + 2], 16) for index in (1, 3, 5))
        colors.append(0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue))
    lighter, darker = sorted(colors, reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def check_accessibility_contract(root: Path) -> None:
    css = (root / "site/assets/site.css").read_text(encoding="utf-8")
    required_css = ".callout > .kicker {\n  color: #284b50;\n}"
    if required_css not in css:
        fail("callout kicker color must remain explicitly scoped to the paper surface")
    ratio = contrast_ratio("#284b50", "#ece5d2")
    if ratio < 4.5:
        fail(f"callout kicker contrast is below WCAG AA: {ratio:.2f}:1")

    index = (root / "site/index.html").read_text(encoding="utf-8")
    if '<ul class="metrics" aria-labelledby="status-title">' not in index:
        fail("metrics must be a named semantic list")
    for relative in ("site/index.html", "site/method/index.html", "site/roadmap/index.html"):
        text = (root / relative).read_text(encoding="utf-8")
        if '<div class="circuit"' in text or '<div class="metrics"' in text:
            fail(f"generic metric/circuit container forbidden in {relative}")
        if '<ol class="circuit" aria-labelledby=' not in text:
            fail(f"circuit must be an ordered list named by a visible heading in {relative}")


def check_status(root: Path) -> None:
    status_path = root / "site/data/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status != EXPECTED_STATUS:
        fail("status snapshot drifted from the complete reviewed schema")

    index = (root / "site/index.html").read_text(encoding="utf-8")
    if 'data-status="proposed"' not in index or "not cut over" not in index:
        fail("proposed live endpoint must stay visibly held")
    visible_markers = ("4 / 13", "20,298", "4 / 34", "98.1%", "18 / 75")
    if any(marker not in index for marker in visible_markers):
        fail("visible status metrics drifted from the reviewed snapshot")


def check_workflow(root: Path) -> None:
    workflow = (root / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    actions = tuple(re.findall(r"uses:\s*([^\s#]+)", workflow))
    if actions != EXPECTED_ACTIONS:
        fail("workflow action inventory or immutable pins changed")
    required = (
        "github.event_name != 'pull_request'",
        "fetch-depth: 0",
        "github.event.pull_request.head.sha || github.sha",
        "python3 -m unittest discover",
        "python3 scripts/check_site.py",
    )
    if any(marker not in workflow for marker in required):
        fail("workflow no longer enforces full-history PR validation without deployment")


def check_history(root: Path) -> None:
    if not (root / ".git").is_dir():
        fail("full Git metadata is required for commit identity validation")
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "log",
            "--all",
            "--format=%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1e",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    records = [record.strip() for record in result.stdout.split("\x1e") if record.strip()]
    if not records:
        fail("public repository history is empty")
    for record in records:
        commit, author_name, author_email, committer_name, committer_email = record.split("\x1f")
        if (
            author_name != AUTOMATION_NAME
            or author_email != AUTOMATION_EMAIL
            or committer_name != AUTOMATION_NAME
            or committer_email != AUTOMATION_EMAIL
        ):
            fail(f"non-automation commit identity remains reachable: {commit}")


def validate(root: Path, *, include_history: bool = True) -> tuple[int, int]:
    root = root.resolve()
    site = root / "site"
    if not site.is_dir() or site.is_symlink():
        fail("site must be a real directory")
    if (site / "CNAME").exists():
        fail("custom-domain cutover is intentionally held")

    files = public_files(root)
    check_inventory(root, files)
    check_disclosures(root, files)
    documents = check_documents(root)
    check_accessibility_contract(root)
    check_status(root)
    check_workflow(root)
    if include_history:
        check_history(root)
    return len(files), len(documents)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="test-fixture mode only; production validation must inspect full Git history",
    )
    args = parser.parse_args(argv)
    files, documents = validate(args.root, include_history=not args.skip_history)
    print(
        f"dossier checks passed: {files} repository files, "
        f"{documents} HTML documents, base {BASE_PATH}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        AssertionError,
        json.JSONDecodeError,
        OSError,
        subprocess.CalledProcessError,
        UnicodeError,
        ValueError,
    ) as error:
        print(f"dossier check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
