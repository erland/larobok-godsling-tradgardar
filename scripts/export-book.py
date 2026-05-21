#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess
import sys
import shutil

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "docs" / "export-metadata.yaml"
BUILD = ROOT / "build"
EXPORTS = ROOT / "exports"

def read_text(path):
    return path.read_text(encoding="utf-8")

def parse_simple_yaml(path):
    """Small YAML reader for this project's simple metadata file.
    Uses PyYAML if available, otherwise falls back to a narrow parser.
    """
    try:
        import yaml
        return yaml.safe_load(read_text(path))
    except Exception:
        data = {}
        chapters = []
        in_chapters = False
        for raw in read_text(path).splitlines():
            line = raw.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if line.startswith("chapters:"):
                in_chapters = True
                continue
            if in_chapters:
                if line.startswith("  - "):
                    chapters.append(line[4:].strip().strip('"'))
                    continue
                if re.match(r"^\S", line):
                    in_chapters = False
            if not in_chapters and ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip('"')
        data["chapters"] = chapters
        return data

def validate_markdown(path, text):
    errors = []

    if re.search(r"^####", text, re.MULTILINE):
        errors.append("innehåller H4-rubrik eller djupare")

    if text.count("```") % 2 != 0:
        errors.append("har ojämnt antal kodblockmarkörer")

    headings = re.findall(r"^# ", text, re.MULTILINE)
    if len(headings) != 1:
        errors.append("ska ha exakt en H1-rubrik")

    # Basic table validation
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "|" in line and line.strip().startswith("|"):
            if i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[i+1]):
                header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
                sep_cells = [c.strip() for c in lines[i+1].strip().strip("|").split("|")]
                if len(header_cells) != len(sep_cells):
                    errors.append(f"tabell på rad {i+1} har olika antal celler i header och separator")
            elif i > 0 and re.match(r"^\s*\|?\s*:?-{3,}:?", line):
                pass

    return errors

def ensure_pandoc():
    return shutil.which("pandoc") is not None

def run(cmd, label):
    print(f"\n{label}")
    print(" ".join(str(c) for c in cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"{label} misslyckades med kod {result.returncode}")

def main():
    if not META.exists():
        raise SystemExit("Saknar docs/export-metadata.yaml")

    meta = parse_simple_yaml(META)
    required = ["title", "author", "language", "chapters"]
    missing = [key for key in required if not meta.get(key)]
    if missing:
        raise SystemExit("Saknar metadatafält: " + ", ".join(missing))

    BUILD.mkdir(exist_ok=True)
    EXPORTS.mkdir(exist_ok=True)

    combined = []
    all_errors = []

    for chapter in meta["chapters"]:
        path = ROOT / chapter
        if not path.exists():
            all_errors.append(f"Saknat kapitel: {chapter}")
            continue

        text = read_text(path)
        errors = validate_markdown(path, text)
        for error in errors:
            all_errors.append(f"{chapter}: {error}")
        combined.append(text.strip())

    if all_errors:
        print("Valideringsfel:")
        for error in all_errors:
            print("- " + error)
        raise SystemExit(1)

    book_md = BUILD / "book.md"
    book_md.write_text("\n\n".join(combined) + "\n", encoding="utf-8")

    # Always create combined markdown for proofreading.
    shutil.copy2(book_md, EXPORTS / "book.md")

    if not ensure_pandoc():
        print("Pandoc hittades inte. Sammanslagen Markdown skapades ändå: exports/book.md")
        print("Installera Pandoc för EPUB/PDF/DOCX-export.")
        return

    title = meta["title"]
    subtitle = meta.get("subtitle", "")
    author = meta["author"]
    lang = meta["language"]
    cover = meta.get("cover_image", "")
    cover_path = ROOT / cover if cover else None

    epub_cmd = [
        "pandoc", str(book_md),
        "--from=gfm",
        "--to=epub3",
        "--toc",
        "--toc-depth=3",
        "--metadata", f"title={title}",
        "--metadata", f"subtitle={subtitle}",
        "--metadata", f"author={author}",
        "--metadata", f"lang={lang}",
        "--css=styles/epub.css",
        "--output", str(EXPORTS / "book.epub")
    ]

    if cover_path and cover_path.exists():
        epub_cmd.insert(-2, f"--epub-cover-image={cover}")

    pdf_cmd = [
        "pandoc", str(book_md),
        "--from=gfm",
        "--toc",
        "--toc-depth=3",
        "--pdf-engine=xelatex",
        "--metadata", f"title={title}",
        "--metadata", f"subtitle={subtitle}",
        "--metadata", f"author={author}",
        "--metadata", f"lang={lang}",
        "--output", str(EXPORTS / "book.pdf")
    ]

    docx_cmd = [
        "pandoc", str(book_md),
        "--from=gfm",
        "--toc",
        "--toc-depth=3",
        "--metadata", f"title={title}",
        "--metadata", f"author={author}",
        "--metadata", f"lang={lang}",
        "--output", str(EXPORTS / "book.docx")
    ]

    run(epub_cmd, "Skapar EPUB")
    try:
        run(pdf_cmd, "Skapar PDF")
    except SystemExit:
        print("PDF-export misslyckades. Kontrollera att xelatex/MacTeX/TinyTeX finns installerat.")
    run(docx_cmd, "Skapar DOCX")

    print("\nExport klar. Filer finns i exports/.")

if __name__ == "__main__":
    main()
