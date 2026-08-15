#!/usr/bin/env python3
"""把旧版 sources 相对路径安全迁移为带引号的 Obsidian Wiki 链接。"""

from __future__ import annotations

import argparse
import codecs
import json
import re
import sys
from pathlib import Path


PAGE_DIRS = {"concepts", "claims", "domains", "syntheses", "ingests", "summaries"}
SOURCE_WIKILINK_RE = re.compile(r"^\[\[([^\[\]|#]+)(?:\|[^\[\]]+)?\]\]$")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?(?:\r?\n)?$")
LIST_LINE_RE = re.compile(r"^(\s+-\s*)(.*?)(\r\n|\n|\r)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="预览或执行 sources 相对路径到 Obsidian Wiki 链接的迁移。"
    )
    parser.add_argument("vault", nargs="?", default=".", help="目标 Vault。")
    parser.add_argument(
        "--scope",
        help="可选范围，如 claims、wiki/claims 或 wiki 内具体 Markdown。",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="执行预览中的安全迁移；省略时不写入任何文件。",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出。")
    return parser.parse_args()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def clean_scalar(value: str) -> tuple[str, bool]:
    value = value.strip()
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
    return (value[1:-1] if quoted else value), quoted


def resolve_scope(wiki: Path, raw_scope: str | None) -> Path:
    if raw_scope is None:
        return wiki
    alias = raw_scope.strip().replace("\\", "/").strip("/")
    if alias.startswith("wiki/"):
        alias = alias[5:]
    candidate = wiki / alias
    resolved = candidate.resolve()
    if not is_within(resolved, wiki) or not candidate.exists():
        raise ValueError("范围不存在或超出 wiki/。")
    return candidate


def source_pages(wiki: Path, scope: Path) -> list[Path]:
    candidates = [scope] if scope.is_file() else sorted(scope.rglob("*.md"))
    pages: list[Path] = []
    for page in candidates:
        if page.suffix.lower() != ".md":
            continue
        try:
            relative = page.relative_to(wiki)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] in PAGE_DIRS:
            pages.append(page)
    return pages


def validate_target(value: str, vault: Path, wiki: Path) -> tuple[str | None, str | None]:
    normalized = value.strip().replace("\\", "/")
    if re.match(r"^(?:https?://|[A-Za-z]:/|/)", normalized, re.IGNORECASE):
        return None, "来源必须使用 Vault 相对目标"
    if ".." in Path(normalized).parts:
        return None, "来源不得包含 .."
    if not normalized.lower().endswith(".md"):
        return None, "来源必须是 Markdown"
    target = (vault / normalized).resolve()
    if not is_within(target, vault):
        return None, "来源超出 Vault"
    if is_within(target, wiki):
        return None, "不得把 wiki 页面作为 sources"
    if not target.is_file():
        return None, "来源不存在"
    return normalized, None


def migrate_text(
    text: str, page: Path, vault: Path, wiki: Path
) -> tuple[str, list[dict[str, object]], list[dict[str, object]]]:
    lines = text.splitlines(keepends=True)
    changes: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    if not lines or lines[0].strip() != "---":
        return text, changes, errors
    try:
        frontmatter_end = next(
            index for index in range(1, len(lines)) if lines[index].strip() == "---"
        )
    except StopIteration:
        return text, changes, errors

    in_sources = False
    for index in range(1, frontmatter_end):
        line = lines[index]
        key_match = KEY_RE.match(line)
        if key_match:
            key, inline_value = key_match.groups()
            in_sources = key == "sources" and not (inline_value or "").strip()
            continue
        if not in_sources:
            continue
        list_match = LIST_LINE_RE.match(line)
        if not list_match:
            continue
        prefix, raw_value, ending = list_match.groups()
        scalar, quoted = clean_scalar(raw_value)
        wiki_match = SOURCE_WIKILINK_RE.fullmatch(scalar)
        if wiki_match and quoted:
            continue
        target_value = wiki_match.group(1).strip() if wiki_match else scalar
        normalized, error = validate_target(target_value, vault, wiki)
        if error:
            errors.append(
                {
                    "path": page.relative_to(vault).as_posix(),
                    "line": index + 1,
                    "value": raw_value.strip(),
                    "message": error,
                }
            )
            continue
        rendered_link = scalar if wiki_match else f"[[{normalized}]]"
        replacement = json.dumps(rendered_link, ensure_ascii=False)
        lines[index] = f"{prefix}{replacement}{ending or ''}"
        changes.append(
            {
                "path": page.relative_to(vault).as_posix(),
                "line": index + 1,
                "from": raw_value.strip(),
                "to": replacement,
            }
        )
    return "".join(lines), changes, errors


def emit(result: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"状态：{result['status']}")
    print(f"待迁移：{result['change_count']} 项，涉及 {len(result['changed_files'])} 个文件。")
    for change in result["changes"]:
        print(
            f"  - {change['path']}:{change['line']} "
            f"{change['from']} -> {change['to']}"
        )
    for error in result["errors"]:
        print(
            f"[阻断] {error['path']}:{error['line']} "
            f"{error['message']}：{error['value']}"
        )
    if result["status"] == "preview":
        print("未写入。确认预览后追加 --apply。")
    elif result["status"] == "blocked":
        print("存在阻断项，未写入任何文件。")


def main() -> int:
    args = parse_args()
    vault = Path(args.vault).expanduser().resolve()
    wiki_entry = vault / "wiki"
    wiki = wiki_entry.resolve()
    if not vault.is_dir():
        print(f"错误：Vault 不存在或不是目录：{vault}", file=sys.stderr)
        return 1
    if wiki_entry.is_symlink() or not wiki.is_dir():
        print(f"错误：wiki/ 不存在、不是目录或为符号链接：{wiki_entry}", file=sys.stderr)
        return 1
    try:
        scope = resolve_scope(wiki, args.scope)
    except ValueError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1

    plans: list[tuple[Path, bytes]] = []
    changes: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for page in source_pages(wiki, scope):
        if page.is_symlink():
            errors.append(
                {
                    "path": page.relative_to(vault).as_posix(),
                    "line": 0,
                    "value": "",
                    "message": "Wiki 页面不能是符号链接",
                }
            )
            continue
        payload = page.read_bytes()
        has_bom = payload.startswith(codecs.BOM_UTF8)
        try:
            text = payload.decode("utf-8-sig")
        except UnicodeDecodeError:
            errors.append(
                {
                    "path": page.relative_to(vault).as_posix(),
                    "line": 0,
                    "value": "",
                    "message": "文件不是可读取的 UTF-8",
                }
            )
            continue
        migrated, page_changes, page_errors = migrate_text(text, page, vault, wiki)
        changes.extend(page_changes)
        errors.extend(page_errors)
        if page_changes:
            encoded = migrated.encode("utf-8")
            plans.append((page, (codecs.BOM_UTF8 if has_bom else b"") + encoded))

    if errors:
        status = "blocked"
    elif args.apply and plans:
        for page, payload in plans:
            page.write_bytes(payload)
        status = "migrated"
    elif plans:
        status = "preview"
    else:
        status = "no-changes"
    result = {
        "status": status,
        "vault": str(vault),
        "scope": str(scope),
        "applied": status == "migrated",
        "change_count": len(changes),
        "changed_files": sorted({change["path"] for change in changes}),
        "changes": changes,
        "errors": errors,
    }
    emit(result, args.json)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
