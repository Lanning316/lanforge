#!/usr/bin/env python3
"""对 Constellate Wiki 执行零依赖的结构、内容充分性与图约束检查。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


PAGE_DIR_TYPES = {
    "concepts": "concept",
    "claims": "claim",
    "domains": "domain",
    "syntheses": "synthesis",
    "ingests": "ingest",
    "summaries": "summary",
}
KNOWLEDGE_TYPES = {"concept", "claim", "domain", "synthesis", "summary"}
CORE_TYPES = {"concept", "claim", "domain", "synthesis"}
CONTENT_TYPES = {"concept", "claim", "domain", "synthesis", "summary"}
CORE_DIRS = {name for name, page_type in PAGE_DIR_TYPES.items() if page_type in CORE_TYPES}
OUTPUT_DIRS = {"concepts", "claims", "domains", "syntheses", "summaries"}
REQUIRED_FIELDS = {
    "concept": {"type", "tags", "created", "updated", "sources"},
    "domain": {"type", "tags", "created", "updated", "sources"},
    "summary": {"type", "tags", "created", "updated", "sources"},
    "claim": {"type", "tags", "state", "origin", "created", "updated", "sources"},
    "synthesis": {"type", "tags", "state", "created", "updated", "sources"},
    "ingest": {"type", "status", "review", "created", "sources", "outputs"},
}
ALLOWED_VALUES = {
    ("claim", "state"): {"proposed", "supported", "contested", "superseded"},
    ("claim", "origin"): {"personal", "source", "synthesis", "conversation"},
    ("synthesis", "state"): {"provisional", "stable", "contested"},
    ("ingest", "status"): {"completed", "partial", "cancelled"},
    ("ingest", "review"): {"accepted", "revised", "rejected"},
}
REQUIRED_SECTIONS = {
    "concept": {"定义", "边界", "语义关系", "依据与来源", "不确定性", "演化记录"},
    "claim": {
        "主张", "含义与适用范围", "支持证据", "质疑与反例", "语义关系",
        "当前状态", "不确定性", "演化记录",
    },
    "domain": {
        "范围", "知识地图", "核心问题", "主要页面", "语义关系",
        "依据与来源", "知识缺口", "演化记录",
    },
    "synthesis": {
        "综合结论", "连接如何形成", "证据链", "竞争性解释", "语义关系",
        "不确定性与缺口", "演化记录",
    },
    "summary": {
        "为什么需要独立摘要", "来源概览", "关键内容", "关联",
        "依据与来源", "局限", "演化记录",
    },
    "ingest": {
        "结果摘要", "输入来源", "各来源关键点", "拟议连接及依据",
        "接受、调整与放弃", "用户纠正", "实际改动", "矛盾、不确定性与限制",
        "外部来源", "检查",
    },
}
RELATION_TYPES = {
    "supports", "challenges", "qualifies", "depends-on", "causes",
    "applies-to", "part-of", "distinguishes-from", "organizes",
    "synthesizes", "supersedes",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$"
)
LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$")
LIST_RE = re.compile(r"^\s+-\s*(.*)$")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
RELATION_RE = re.compile(
    r"^\s*-\s+\*\*([a-z-]+)\*\*\s*→\s*"
    r"\[([^\]]+)\]\(([^)]+)\)\s*[：:]\s*(\S.*)$"
)
ACCESS_DATE_RE = re.compile(r"(?:访问于|accessed\s+(?:on\s+)?)\s*\d{4}-\d{2}-\d{2}", re.I)
CONTENT_FLOOR_ROW_RE = re.compile(
    r"^\|\s*`?(concept|claim|domain|synthesis|summary)`?\s*"
    r"\|\s*(\d+)\s*\|"
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
LATIN_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*")
SOURCE_WIKILINK_RE = re.compile(r"^\[\[([^\[\]|#]+)(?:\|[^\[\]]+)?\]\]$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查 Constellate Wiki 的 schema、内容充分性、证据路径、链接、索引和语义图。"
    )
    parser.add_argument("vault", nargs="?", default=".", help="目标 Vault。")
    parser.add_argument(
        "--scope",
        help="可选范围，如 claims、wiki/claims 或 wiki 内具体路径。",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 输出。")
    return parser.parse_args()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def in_scope(path: Path, scope: Path) -> bool:
    path = path.resolve()
    scope = scope.resolve()
    return path == scope if scope.is_file() else is_within(path, scope)


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, object] | None, str, list[str]]:
    lines = text.splitlines()
    errors: list[str] = []
    if not lines or lines[0].strip() != "---":
        return None, text, ["缺少起始 YAML frontmatter。"]

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text, ["frontmatter 缺少结束分隔线。"]

    data: dict[str, object] = {}
    current_key: str | None = None
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key_match = KEY_RE.match(line)
        if key_match:
            key, raw = key_match.groups()
            if key in data:
                errors.append(f"frontmatter 第 {number} 行重复字段：{key}。")
                current_key = None
                continue
            raw = (raw or "").strip()
            if raw == "[]":
                data[key] = []
                current_key = None
            elif raw:
                data[key] = clean_scalar(raw)
                current_key = None
            else:
                data[key] = []
                current_key = key
            continue
        list_match = LIST_RE.match(line)
        if list_match and current_key:
            raw_value = list_match.group(1).strip()
            if (
                current_key == "sources"
                and raw_value.startswith("[[")
                and raw_value.endswith("]]")
            ):
                errors.append(f"frontmatter 第 {number} 行的 sources Wiki 链接必须用引号包裹。")
            value = clean_scalar(raw_value)
            cast_list = data[current_key]
            if isinstance(cast_list, list):
                cast_list.append(value)
            continue
        errors.append(f"frontmatter 第 {number} 行不属于支持的简单 YAML 结构。")
        current_key = None

    return data, "\n".join(lines[end + 1 :]), errors


def markdown_targets(text: str, source_file: Path) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = []
    for match in LINK_RE.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1]
        if re.match(r"^(?:https?://|mailto:|obsidian:)", raw, re.IGNORECASE):
            continue
        if raw.startswith("#"):
            continue
        destination = unquote(raw.split("#", 1)[0].split("?", 1)[0]).strip()
        if not destination:
            continue
        targets.append((match.group(1), (source_file.parent / destination).resolve()))
    return targets


def without_fenced_blocks(text: str) -> str:
    visible: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            visible.append("")
        else:
            visible.append("" if in_fence else line)
    return "\n".join(visible)


def main() -> int:
    args = parse_args()
    vault = Path(args.vault).expanduser().resolve()
    wiki_entry = vault / "wiki"
    wiki = wiki_entry.resolve()
    issues: list[dict[str, str]] = []

    def add(severity: str, code: str, path: Path | str, message: str) -> None:
        if isinstance(path, Path):
            try:
                shown = path.relative_to(vault).as_posix()
            except ValueError:
                shown = str(path)
        else:
            shown = path
        issues.append(
            {"severity": severity, "code": code, "path": shown, "message": message}
        )

    if not vault.is_dir():
        add("error", "vault-missing", vault, "Vault 不存在或不是目录。")
    if wiki_entry.is_symlink():
        add("error", "wiki-symlink", wiki_entry, "拒绝检查符号链接 wiki/。")
    if not wiki.is_dir():
        add("error", "wiki-missing", wiki, "wiki/ 不存在或不是目录。")
    if issues:
        return finish(vault, wiki, issues, args.json)

    content_floors = load_content_floors(wiki)

    for base_name in ("schema.md", "index.md", "log.md"):
        if not (wiki / base_name).is_file():
            add("error", "base-file-missing", wiki / base_name, "缺少基础文件。")

    scan_root = wiki
    if args.scope:
        alias = args.scope.strip().replace("\\", "/").strip("/")
        if alias.startswith("wiki/"):
            alias = alias[5:]
        candidate = (wiki / alias).resolve()
        if not is_within(candidate, wiki) or not candidate.exists():
            add("error", "scope-invalid", args.scope, "范围不存在或超出 wiki/。")
            return finish(vault, wiki, issues, args.json)
        scan_root = candidate

    if scan_root.is_file():
        page_files = [scan_root] if scan_root.suffix.lower() == ".md" else []
    else:
        page_files = sorted(scan_root.rglob("*.md"))

    parsed: dict[Path, tuple[dict[str, object], str]] = {}
    knowledge_pages: list[Path] = []

    for page in page_files:
        if page.is_symlink():
            add("error", "page-symlink", page, "Wiki 页面不能是符号链接。")
            continue
        relative = page.relative_to(wiki)
        if relative.as_posix() in {"schema.md", "index.md", "log.md"}:
            continue
        if not relative.parts or relative.parts[0] not in PAGE_DIR_TYPES:
            add("warning", "unknown-location", page, "Markdown 不在已知页面类型目录中。")
            continue

        expected_type = PAGE_DIR_TYPES[relative.parts[0]]
        try:
            text = page.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            add("error", "encoding", page, "文件不是可读取的 UTF-8。")
            continue

        frontmatter, body, parse_errors = parse_frontmatter(text)
        for message in parse_errors:
            add("error", "frontmatter-parse", page, message)
        if frontmatter is None:
            continue
        parsed[page.resolve()] = (frontmatter, body)

        page_type = frontmatter.get("type")
        if page_type != expected_type:
            add(
                "error",
                "type-location-mismatch",
                page,
                f"目录要求 type: {expected_type}，实际为 {page_type!r}。",
            )
            continue

        missing = REQUIRED_FIELDS[expected_type] - set(frontmatter)
        for field in sorted(missing):
            add("error", "required-field", page, f"缺少必填字段：{field}。")

        for (type_name, field), allowed in ALLOWED_VALUES.items():
            if expected_type == type_name and field in frontmatter:
                value = frontmatter[field]
                if value not in allowed:
                    add(
                        "error",
                        "enum",
                        page,
                        f"{field} 必须是 {sorted(allowed)} 之一，实际为 {value!r}。",
                    )

        created = frontmatter.get("created")
        expected_date = DATETIME_RE if expected_type == "ingest" else DATE_RE
        if created is not None and (
            not isinstance(created, str) or not expected_date.fullmatch(created)
        ):
            label = "ISO 8601 带时区时间" if expected_type == "ingest" else "YYYY-MM-DD"
            add("error", "created-format", page, f"created 必须使用 {label}。")

        if expected_type != "ingest":
            updated = frontmatter.get("updated")
            if updated is not None and (
                not isinstance(updated, str) or not DATE_RE.fullmatch(updated)
            ):
                add("error", "updated-format", page, "updated 必须使用 YYYY-MM-DD。")
            if (
                isinstance(created, str)
                and isinstance(updated, str)
                and DATE_RE.fullmatch(created)
                and DATE_RE.fullmatch(updated)
                and updated < created
            ):
                add("error", "date-order", page, "updated 不能早于 created。")

        check_title_and_sections(body, expected_type, page, add)

        sources = frontmatter.get("sources")
        if not isinstance(sources, list):
            add("error", "sources-list", page, "sources 必须使用 YAML 列表。")
        else:
            check_sources(sources, page, vault, wiki, add)

        if expected_type in KNOWLEDGE_TYPES:
            knowledge_pages.append(page.resolve())
            tags = frontmatter.get("tags")
            check_tags(tags, expected_type, page, add)
            check_content_sufficiency(
                body, expected_type, page, content_floors, add
            )
            check_evolution(body, page, vault, wiki, add)
            check_external_sources(body, page, add)

        if expected_type == "ingest":
            outputs = frontmatter.get("outputs")
            status = frontmatter.get("status")
            review = frontmatter.get("review")
            check_outputs(outputs, status, review, page, vault, wiki, add)

        for raw, target in markdown_targets(without_fenced_blocks(text), page):
            if not is_within(target, vault):
                add("error", "link-outside-vault", page, f"本地链接超出 Vault：{raw}")
            elif not target.exists():
                add("error", "broken-link", page, f"本地链接不存在：{raw}")

    check_catalog_collisions(wiki, scan_root, add)
    graph = check_relation_graph(wiki, scan_root, add)
    check_index(wiki, knowledge_pages, parsed, add)
    check_log(wiki, add)
    return finish(vault, wiki, issues, args.json, graph)


def check_title_and_sections(body: str, page_type: str, page: Path, add) -> None:
    visible = without_fenced_blocks(body)
    titles = H1_RE.findall(visible)
    if len(titles) != 1:
        add("error", "h1-count", page, f"正文必须恰好包含一个 H1，实际为 {len(titles)} 个。")
    elif page_type != "ingest" and titles[0].strip() != page.stem:
        add("error", "title-filename", page, "H1 标题必须与文件名一致。")
    if page_type == "ingest" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}-.+", page.stem):
        add("error", "ingest-filename", page, "ingest 文件名必须使用 YYYY-MM-DD-简短标题。")

    headings = {heading.strip() for heading in H2_RE.findall(visible)}
    for section in sorted(REQUIRED_SECTIONS[page_type] - headings):
        add("error", "required-section", page, f"缺少必需二级标题：{section}。")


def check_external_sources(body: str, page: Path, add) -> None:
    in_fence = False
    for number, line in enumerate(body.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not re.search(r"\]\(https?://", line, re.I):
            continue
        if not ACCESS_DATE_RE.search(line):
            add(
                "warning",
                "external-access-date",
                page,
                f"正文第 {number} 行的外部来源缺少 YYYY-MM-DD 访问日期。",
            )


def check_tags(tags: object, page_type: str, page: Path, add) -> None:
    if not isinstance(tags, list):
        add("error", "tags-list", page, "tags 必须使用 YAML 列表。")
        return
    if not tags:
        add("warning", "tags-empty", page, "tags 为空；确认确实没有稳定检索价值的标签。")
    seen: set[str] = set()
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            add("error", "tag-empty", page, "标签必须是非空字符串。")
            continue
        if "/" in tag:
            add("error", "tag-nested", page, f"标签必须为单层：{tag}")
        if tag.strip().casefold() == page_type:
            add("warning", "tag-repeats-type", page, f"标签不应重复页面 type：{tag}")
        key = tag.casefold()
        if key in seen:
            add("error", "tag-duplicate", page, f"存在重复标签：{tag}")
        seen.add(key)
    if len(tags) > 3:
        add("warning", "tags-many", page, "标签超过 3 个；这不是硬错误，请确认每个标签都有稳定检索价值。")


def check_sources(
    sources: list[object], page: Path, vault: Path, wiki: Path, add
) -> None:
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, str) or not source.strip():
            add("error", "source-empty", page, "sources 中存在空值。")
            continue
        match = SOURCE_WIKILINK_RE.fullmatch(source.strip())
        legacy_path = match is None
        normalized = (
            match.group(1).strip() if match else source.strip()
        ).replace("\\", "/")
        if re.match(r"^(?:https?://|[A-Za-z]:/|/)", normalized):
            add("error", "source-not-relative", page, f"来源必须使用 Vault 相对目标：{source}")
            continue
        parts = Path(normalized).parts
        if ".." in parts:
            add("error", "source-traversal", page, f"来源不得包含 ..：{source}")
            continue
        if not normalized.lower().endswith(".md"):
            add("error", "source-not-markdown", page, f"来源必须是 Markdown：{source}")
            continue
        target = (vault / normalized).resolve()
        valid = True
        if not is_within(target, vault):
            add("error", "source-outside-vault", page, f"来源超出 Vault：{source}")
            valid = False
        elif is_within(target, wiki):
            add("error", "source-in-wiki", page, f"不得把 wiki 页面作为 sources：{source}")
            valid = False
        elif not target.is_file():
            add("error", "source-missing", page, f"来源不存在：{source}")
            valid = False
        key = normalized.casefold()
        if key in seen:
            add("error", "source-duplicate", page, f"重复来源：{source}")
            valid = False
        seen.add(key)
        if legacy_path and valid:
            add(
                "warning", "source-legacy-path", page,
                f'旧版 sources 相对路径仍可读取，建议迁移为 "[[{normalized}]]"：{source}',
            )


def check_outputs(
    outputs: object,
    status: object,
    review: object,
    page: Path,
    vault: Path,
    wiki: Path,
    add,
) -> None:
    if not isinstance(outputs, list):
        add("error", "outputs-list", page, "outputs 必须使用 YAML 列表。")
        return
    if (status == "cancelled" or review == "rejected") and outputs:
        add("error", "audit-outputs", page, "取消或否决的兼容审计记录必须使用空 outputs。")
    if (status == "cancelled") != (review == "rejected"):
        add("error", "audit-state", page, "兼容审计记录必须同时使用 status: cancelled 与 review: rejected。")
    if status == "completed" and review in {"accepted", "revised"} and not outputs:
        add("error", "completed-outputs-empty", page, "已完成的 ingest 必须列出实际输出。")

    seen: set[str] = set()
    for output in outputs:
        if not isinstance(output, str) or not output.strip():
            add("error", "output-empty", page, "outputs 中存在空值。")
            continue
        normalized = output.replace("\\", "/")
        if re.match(r"^(?:[A-Za-z]:/|/)", normalized) or ".." in Path(normalized).parts:
            add("error", "output-not-relative", page, f"输出必须是 Vault 相对路径：{output}")
            continue
        target = (vault / normalized).resolve()
        if not is_within(target, wiki):
            add("error", "output-outside-wiki", page, f"输出必须位于 wiki/：{output}")
        elif not target.is_file():
            add("error", "output-missing", page, f"输出不存在：{output}")
        elif target.relative_to(wiki).parts[0] not in OUTPUT_DIRS:
            add("error", "output-not-page", page, f"outputs 只列知识页或 summary：{output}")
        key = normalized.casefold()
        if key in seen:
            add("error", "output-duplicate", page, f"重复输出：{output}")
        seen.add(key)


def read_catalog(wiki: Path, directories: set[str]) -> dict[Path, tuple[str, dict[str, object], str]]:
    catalog: dict[Path, tuple[str, dict[str, object], str]] = {}
    for directory in sorted(directories):
        root = wiki / directory
        if not root.is_dir():
            continue
        for page in sorted(root.rglob("*.md")):
            if page.is_symlink():
                continue
            try:
                data, body, errors = parse_frontmatter(page.read_text(encoding="utf-8-sig"))
            except UnicodeDecodeError:
                continue
            expected = PAGE_DIR_TYPES[directory]
            if data is not None and not errors and data.get("type") == expected:
                catalog[page.resolve()] = (expected, data, body)
    return catalog


def check_catalog_collisions(wiki: Path, scope: Path, add) -> None:
    catalog = read_catalog(wiki, OUTPUT_DIRS)
    titles: dict[str, list[Path]] = {}
    tags: dict[str, list[tuple[str, Path]]] = {}
    for page, (_, data, body) in catalog.items():
        matches = H1_RE.findall(without_fenced_blocks(body))
        if matches:
            titles.setdefault(matches[0].strip().casefold(), []).append(page)
        for tag in data.get("tags", []):
            if isinstance(tag, str) and tag.strip():
                key = re.sub(r"[\s_-]+", "", tag).casefold()
                tags.setdefault(key, []).append((tag, page))

    for pages in titles.values():
        if len(pages) > 1:
            names = "、".join(page.relative_to(wiki).as_posix() for page in pages)
            for page in pages:
                if in_scope(page, scope):
                    add("error", "title-duplicate", page, f"多个页面使用相同 H1：{names}")
    for variants in tags.values():
        spellings = {tag for tag, _ in variants}
        if len(spellings) <= 1:
            continue
        shown = "、".join(sorted(spellings))
        reported: set[Path] = set()
        for _, page in variants:
            if page not in reported and in_scope(page, scope):
                add("warning", "tag-variant", page, f"存在仅大小写、空格或连接符不同的标签：{shown}")
                reported.add(page)


def section_lines(body: str, title: str) -> list[str] | None:
    lines = without_fenced_blocks(body).splitlines()
    start = next(
        (i + 1 for i, line in enumerate(lines) if line.strip() == f"## {title}"),
        None,
    )
    if start is None:
        return None
    end = next(
        (i for i in range(start, len(lines)) if re.match(r"^#{1,2}\s+", lines[i])),
        len(lines),
    )
    return lines[start:end]


def parse_content_floors(schema: Path) -> dict[str, int]:
    try:
        text = schema.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return {}
    lines = section_lines(text, "内容充分性")
    if lines is None:
        return {}
    floors: dict[str, int] = {}
    for line in lines:
        match = CONTENT_FLOOR_ROW_RE.match(line)
        if match:
            floors[match.group(1)] = int(match.group(2))
    return floors


def load_content_floors(wiki: Path) -> dict[str, int]:
    local = parse_content_floors(wiki / "schema.md")
    if CONTENT_TYPES <= set(local):
        return local
    default_schema = (
        Path(__file__).resolve().parent.parent / "assets" / "wiki" / "schema.md"
    )
    defaults = parse_content_floors(default_schema)
    return {**defaults, **local}


def content_units(body: str) -> int:
    visible = without_fenced_blocks(body)
    kept: list[str] = []
    skip_section = False
    for line in visible.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            skip_section = heading.group(1) in {"语义关系", "演化记录"}
            continue
        if skip_section or re.match(r"^#{1,6}\s+", line):
            continue
        cleaned = re.sub(r"\{\{[^{}]+\}\}", " ", line)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"<!--.*?-->", " ", cleaned)
        kept.append(cleaned)
    prose = "\n".join(kept)
    return len(CJK_RE.findall(prose)) + len(LATIN_WORD_RE.findall(prose))


def check_content_sufficiency(
    body: str,
    page_type: str,
    page: Path,
    floors: dict[str, int],
    add,
) -> None:
    floor = floors.get(page_type)
    if floor is None:
        return
    units = content_units(body)
    if units < floor:
        add(
            "warning",
            "content-thin",
            page,
            (
                f"正文约 {units} 个内容单位，低于 {page_type} 的机械预警线 {floor}；"
                "按内容契约补足有来源支撑的模块，或在 ingest 记录来源受限例外。"
            ),
        )


def check_relation_graph(wiki: Path, scope: Path, add) -> dict[str, int]:
    catalog = read_catalog(wiki, CORE_DIRS)
    edges: dict[Path, list[tuple[str, Path]]] = {page: [] for page in catalog}
    for page, (page_type, _, body) in catalog.items():
        lines = section_lines(body, "语义关系")
        if lines is None:
            continue
        seen: set[tuple[str, Path]] = set()
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("<!--"):
                continue
            match = RELATION_RE.fullmatch(line)
            if match is None:
                if in_scope(page, scope):
                    add("error", "relation-format", page, f"语义关系第 {number} 行不符合机器可读格式。")
                continue
            relation, _, raw_target, rationale = match.groups()
            valid = True
            if relation not in RELATION_TYPES:
                if in_scope(page, scope):
                    add("error", "relation-type", page, f"未知关系类型：{relation}")
                valid = False
            if len(LINK_RE.findall(line)) != 1:
                if in_scope(page, scope):
                    add("error", "relation-link-count", page, "一条语义边必须恰好包含一个目标链接。")
                valid = False
            if len(rationale.strip()) < 4:
                if in_scope(page, scope):
                    add("error", "relation-rationale", page, "语义边必须给出可审查的关系理由。")
                valid = False

            raw = raw_target.strip()
            if re.match(r"^(?:https?://|mailto:|obsidian:|#)", raw, re.I):
                target = page
                valid = False
                if in_scope(page, scope):
                    add("error", "relation-target", page, "语义边目标必须是本地核心知识页。")
            else:
                destination = unquote(raw.split("#", 1)[0].split("?", 1)[0]).strip()
                target = (page.parent / destination).resolve()
                if target not in catalog:
                    valid = False
                    if in_scope(page, scope):
                        add("error", "relation-target", page, f"语义边目标不是有效核心知识页：{raw_target}")
            if target == page:
                valid = False
                if in_scope(page, scope):
                    add("error", "relation-self", page, "语义边不能指向当前页自身。")
            edge = (relation, target)
            if edge in seen:
                valid = False
                if in_scope(page, scope):
                    add("error", "relation-duplicate", page, f"重复语义边：{relation} → {target.name}")
            seen.add(edge)

            if relation == "organizes" and page_type != "domain":
                valid = False
                if in_scope(page, scope):
                    add("error", "relation-domain-only", page, "只有 domain 可以发出 organizes 边。")
            if relation == "synthesizes" and page_type != "synthesis":
                valid = False
                if in_scope(page, scope):
                    add("error", "relation-synthesis-only", page, "只有 synthesis 可以发出 synthesizes 边。")
            if relation == "supersedes" and (
                page_type != "claim" or catalog.get(target, (None,))[0] != "claim"
            ):
                valid = False
                if in_scope(page, scope):
                    add("error", "relation-supersedes-type", page, "supersedes 必须从 claim 指向 claim。")
            if valid:
                edges[page].append(edge)
    return evaluate_graph(catalog, edges, wiki, scope, add)


def evaluate_graph(catalog, edges, wiki: Path, scope: Path, add) -> dict[str, int]:
    neighbors: dict[Path, set[Path]] = {page: set() for page in catalog}
    for source, outgoing in edges.items():
        for _, target in outgoing:
            neighbors[source].add(target)
            neighbors[target].add(source)

    node_count = len(catalog)
    for page, (page_type, _, _) in catalog.items():
        if not in_scope(page, scope):
            continue
        outgoing = edges[page]
        if node_count > 1 and not neighbors[page]:
            add(
                "warning", "graph-isolated", page,
                "核心页目前没有有效入边或出边；请人工核对是否确有遗漏，不要为消除警告编造关系。",
            )
        if page_type == "domain" and node_count > 1 and not any(
            relation == "organizes" for relation, _ in outgoing
        ):
            add(
                "warning", "graph-domain-edge", page,
                "domain 目前没有 organizes 出边；请核对其导航职责，不要在无依据时补边。",
            )
        if page_type == "synthesis":
            targets = {target for relation, target in outgoing if relation == "synthesizes"}
            if len(targets) < 2:
                add(
                    "warning", "graph-synthesis-edges", page,
                    "synthesis 当前指向的不同核心页少于两个；请核对综合对象，不要为达到数量编造关系。",
                )

    remaining = set(catalog)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            current = stack.pop()
            reached = neighbors[current] & remaining
            remaining -= reached
            stack.extend(reached)
    if scope.resolve() == wiki.resolve() and node_count > 1 and components > 1:
        add("warning", "graph-components", wiki, f"核心图包含 {components} 个弱连通分量，需要人工判断是否缺少桥接关系。")

    return {
        "nodes": node_count,
        "edges": sum(len(outgoing) for outgoing in edges.values()),
        "components": components,
        "scoped_nodes": sum(in_scope(page, scope) for page in catalog),
    }


def check_evolution(body: str, page: Path, vault: Path, wiki: Path, add) -> None:
    lines = section_lines(body, "演化记录")
    if lines is None:
        return
    ingest_root = (wiki / "ingests").resolve()
    ingest_targets = [
        target
        for _, target in markdown_targets("\n".join(lines), page)
        if is_within(target, ingest_root)
    ]
    if not ingest_targets:
        add("error", "evolution-link", page, "演化记录未链接到 ingests/ 中的记录。")
        return
    page_output = page.relative_to(vault).as_posix().casefold()
    for ingest in ingest_targets:
        if not ingest.is_file():
            continue
        try:
            data, _, _ = parse_frontmatter(ingest.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError:
            continue
        outputs = data.get("outputs") if data else None
        normalized = {
            item.replace(chr(92), '/').casefold()
            for item in outputs or []
            if isinstance(item, str)
        }
        if page_output not in normalized:
            add("error", "evolution-output-backlink", page, f"演化记录所链 ingest 未在 outputs 列出本页：{ingest.name}")


def check_index(
    wiki: Path,
    knowledge_pages: list[Path],
    parsed: dict[Path, tuple[dict[str, object], str]],
    add,
) -> None:
    index = wiki / "index.md"
    if not index.is_file():
        return
    try:
        text = index.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        add("error", "encoding", index, "文件不是可读取的 UTF-8。")
        return

    link_lines: dict[Path, list[str]] = {}
    link_sections: dict[Path, list[str | None]] = {}
    resolved_links: list[Path] = []
    current_section: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current_section = heading.group(1)
        for _, target in markdown_targets(line, index):
            resolved_links.append(target)
            link_lines.setdefault(target, []).append(line)
            link_sections.setdefault(target, []).append(current_section)
    counts: dict[Path, int] = {}
    for target in resolved_links:
        counts[target] = counts.get(target, 0) + 1
        if not target.exists():
            add("error", "index-broken-link", index, f"索引链接不存在：{target.name}")

    for page in knowledge_pages:
        page_data = page.parts
        if not any(part in {"concepts", "claims", "domains", "syntheses"} for part in page_data):
            continue
        count = counts.get(page.resolve(), 0)
        if count == 0:
            add("error", "index-missing", page, "核心知识页未收录到 index.md。")
        elif count > 1:
            add("error", "index-duplicate", page, "核心知识页在 index.md 中重复出现。")
        else:
            entry = link_lines[page.resolve()][0]
            directory = page.relative_to(wiki).parts[0]
            expected_section = {
                "domains": "Domains", "concepts": "Concepts",
                "claims": "Claims", "syntheses": "Syntheses",
            }[directory]
            if link_sections[page.resolve()][0] != expected_section:
                add("error", "index-section", page, f"核心页必须位于 index 的 {expected_section} 分区。")
            if not entry.lstrip().startswith("- ") or " — " not in entry:
                add(
                    "warning",
                    "index-summary-format",
                    page,
                    "索引项应使用列表，并在链接后提供破折号分隔的一句话说明。",
                )
            elif not entry.split(" — ", 1)[1].strip():
                add("warning", "index-summary-empty", page, "索引项的一句话说明为空。")

            frontmatter = parsed.get(page.resolve(), ({}, ""))[0]
            page_type = frontmatter.get("type")
            state = frontmatter.get("state")
            if page_type in {"claim", "synthesis"} and isinstance(state, str):
                if f"状态：{state}" not in entry:
                    add(
                        "warning",
                        "index-state-mismatch",
                        page,
                        f"索引项没有反映当前状态：{state}。",
                    )


def check_log(wiki: Path, add) -> None:
    log = wiki / "log.md"
    if not log.is_file():
        return
    try:
        text = log.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        add("error", "encoding", log, "文件不是可读取的 UTF-8。")
        return
    in_fence = False
    timestamps: list[tuple[str, int]] = []
    headings_seen: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.startswith("## ["):
            continue
        match = re.match(
            r"^## \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\] "
            r"(?:ingest|query|lint|schema|migration|correction) \| .+",
            line,
        )
        if not match:
            add("warning", "log-heading", log, f"第 {line_number} 行日志标题格式不规范。")
            continue
        if line in headings_seen:
            add("warning", "log-duplicate", log, f"第 {line_number} 行重复日志标题。")
        headings_seen.add(line)
        timestamps.append((match.group(1), line_number))
    for previous, current in zip(timestamps, timestamps[1:]):
        if current[0] < previous[0]:
            add("warning", "log-order", log, f"第 {current[1]} 行时间早于上一条日志。")


def finish(
    vault: Path,
    wiki: Path,
    issues: list[dict[str, str]],
    as_json: bool,
    graph: dict[str, int] | None = None,
) -> int:
    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    result = {
        "vault": str(vault),
        "wiki": str(wiki),
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }
    if graph is not None:
        result["graph"] = graph
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"检查完成：{errors} 个错误，{warnings} 个警告。")
        if graph is not None:
            print(
                f"语义图：{graph['nodes']} 个核心节点，{graph['edges']} 条有效边，"
                f"{graph['components']} 个弱连通分量。"
            )
        for issue in issues:
            marker = "错误" if issue["severity"] == "error" else "警告"
            print(f"[{marker}] {issue['path']}：{issue['message']} ({issue['code']})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
