#!/usr/bin/env python3
"""CI-Gate: warnt vor personenbezogenen Daten (E-Mails, IBANs, Telefonnummern)
in Testdaten/Fixtures, bevor sie in main gemerged werden.

Exit-Code 0 = keine Funde, 1 = mindestens ein nicht zugelassener Fund.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".cicd-standards",
    "node_modules",
    "dist",
    "build",
    ".astro",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

SAFE_EMAIL_DOMAINS = {"example.com", "example.net", "example.org", "example.edu", "test", "localhost", "invalid", "local"}
SAFE_EMAIL_SUFFIXES = (".example", ".test", ".invalid", ".localhost")

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IBAN_CANDIDATE_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{2,4}){3,8}\b")
PHONE_RE = re.compile(r"\+49[\s\-]?\d{2,5}[\s\-]?\d{3,10}")

TEXT_FILE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml",
    ".csv", ".tsv", ".txt", ".md", ".sql", ".xml", ".env",
}


@dataclass(frozen=True)
class Finding:
    path: str
    line_no: int
    kind: str
    matched_text: str


def redact(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def is_email_allowlisted(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    if domain in SAFE_EMAIL_DOMAINS:
        return True
    return any(domain.endswith(suffix) for suffix in SAFE_EMAIL_SUFFIXES)


def iban_checksum_valid(candidate: str) -> bool:
    iban = candidate.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    try:
        numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    except ValueError:
        return False
    return int(numeric) % 97 == 1


def load_allowlist(root: Path) -> list:
    allowlist_path = root / ".dsgvo-guard-allowlist"
    patterns: list = []
    if not allowlist_path.exists():
        return patterns
    for raw_line in allowlist_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            patterns.append(re.compile(line[3:]))
        else:
            patterns.append(line)
    return patterns


def is_allowlisted(value: str, allowlist: list) -> bool:
    for entry in allowlist:
        if isinstance(entry, re.Pattern):
            if entry.search(value):
                return True
        elif entry == value:
            return True
    return False


def scan_text(text: str, allowlist: list) -> list:
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "dsgvo-guard: allow" in line:
            continue

        for match in EMAIL_RE.finditer(line):
            email = match.group(0)
            if is_email_allowlisted(email) or is_allowlisted(email, allowlist):
                continue
            findings.append(Finding("", line_no, "email", email))

        for match in IBAN_CANDIDATE_RE.finditer(line):
            candidate = match.group(0)
            if not iban_checksum_valid(candidate):
                continue
            if is_allowlisted(candidate, allowlist):
                continue
            findings.append(Finding("", line_no, "iban", candidate))

        for match in PHONE_RE.finditer(line):
            phone = match.group(0)
            if is_allowlisted(phone, allowlist):
                continue
            findings.append(Finding("", line_no, "phone", phone))

    return findings


def walk_files(root: Path, exclude_dirs: set):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in exclude_dirs for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_FILE_EXTENSIONS:
            continue
        yield path


def scan_file(path: Path, allowlist: list) -> list:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    findings = scan_text(text, allowlist)
    return [Finding(str(path), f.line_no, f.kind, f.matched_text) for f in findings]


def run(root: Path, paths: list | None) -> list:
    allowlist = load_allowlist(root)
    targets = [Path(p) for p in paths] if paths else list(walk_files(root, DEFAULT_EXCLUDE_DIRS))
    findings: list = []
    for path in targets:
        if path.is_file():
            findings.extend(scan_file(path, allowlist))
    return findings


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Wurzelverzeichnis, das durchsucht wird")
    parser.add_argument("--paths", nargs="*", default=None, help="Einzelne Dateien statt vollem Root-Scan (z.B. aus git diff)")
    args = parser.parse_args(argv)

    root = Path(args.root)
    findings = run(root, args.paths)

    if not findings:
        print("DSGVO-Guard: keine verdächtigen Muster gefunden.")
        return 0

    print(f"DSGVO-Guard: {len(findings)} verdächtige(s) Muster gefunden:\n")
    for f in findings:
        print(f"  {f.path}:{f.line_no}: [{f.kind}] {redact(f.matched_text)}")
    print(
        "\nFalls es sich um unkritische Testdaten handelt: "
        "reservierte Domains (example.com/.test/...) nutzen oder in "
        ".dsgvo-guard-allowlist eintragen bzw. Zeile mit '# dsgvo-guard: allow' markieren."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
