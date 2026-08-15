#!/usr/bin/env python3
"""Validate generated Markdown tutorials without third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


PLACEHOLDER_RE = re.compile(r"<[A-Z][A-Z0-9_ -]{1,64}>")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
TAKEAWAY_RE = re.compile(r"💡\s*\*\*一句话记住\*\*")
SOURCE_LOCATION_RE = re.compile(
    r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+:\d+(?:-\d+)?"
)
WINDOWS_ABS_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s)`]+")
USER_HOME_RE = re.compile(r"/(?:Users|home)/[^/\s)]+/")
CODE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _check_fences(text: str) -> list[str]:
    errors: list[str] = []
    active: tuple[str, int, int] | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if not match:
            continue
        marker = match.group(1)
        char = marker[0]
        length = len(marker)
        if active is None:
            active = (char, length, number)
        elif char == active[0] and length >= active[1]:
            active = None
    if active is not None:
        errors.append(f"第 {active[2]} 行开始的 Markdown 围栏没有闭合")
    return errors


def _extract_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    return unquote(target.strip())


def _mode_for(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    lowered = path.name.lower()
    if lowered in {"readme.md", "_spec.md", "_plan.md"} or lowered.startswith(
        "appendix"
    ):
        return "appendix"
    return "single"


def validate(
    path: Path, repo_root: Path, mode: str, text: str | None = None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if text is None and not path.is_file():
        return [f"教程文件不存在：{path}"], warnings

    path = path.resolve()
    repo_root = repo_root.resolve()
    if text is None:
        text = path.read_text(encoding="utf-8")
    content = _strip_comments(text)
    effective_mode = _mode_for(path, mode)

    placeholders = sorted(set(PLACEHOLDER_RE.findall(content)))
    if placeholders:
        errors.append("残留模板占位符：" + ", ".join(placeholders[:12]))

    errors.extend(_check_fences(content))

    if WINDOWS_ABS_RE.search(content):
        errors.append("包含 Windows 本机绝对路径")
    if USER_HOME_RE.search(content):
        errors.append("包含用户主目录绝对路径")

    source_locations = len(SOURCE_LOCATION_RE.findall(content))
    source_links = 0

    for raw_target in LINK_RE.findall(content):
        target = _extract_target(raw_target)
        if not target or PLACEHOLDER_RE.search(target) or target.startswith("#"):
            continue

        parsed = urlparse(target)
        if parsed.scheme in {"http", "https", "mailto"}:
            if parsed.scheme in {"http", "https"}:
                if re.search(r"/(?:blob|-/blob)/(?:main|master)/", target):
                    warnings.append(f"远程链接锚定可变分支：{target}")
                if Path(parsed.path).suffix.lower() in CODE_SUFFIXES:
                    source_links += 1
            continue

        if parsed.scheme == "file":
            errors.append(f"禁止本机文件链接：{target}")
            continue

        path_part = target.split("#", 1)[0].split("?", 1)[0]
        if not path_part:
            continue
        if re.match(r"^[A-Za-z]:[\\/]", path_part) or path_part.startswith(("/", "\\\\")):
            errors.append(f"禁止绝对本地链接：{target}")
            continue

        resolved = (path.parent / path_part).resolve()
        if not _is_within(resolved, repo_root):
            errors.append(f"相对链接逃出项目根目录：{target}")
            continue
        if not resolved.exists():
            errors.append(f"相对链接目标不存在：{target}")
            continue

        if resolved.suffix.lower() in CODE_SUFFIXES:
            source_links += 1
            anchor = re.search(r"#L(\d+)(?:-L(\d+))?", target)
            if anchor and resolved.is_file():
                line_count = len(resolved.read_text(encoding="utf-8", errors="ignore").splitlines())
                end_line = int(anchor.group(2) or anchor.group(1))
                if end_line > line_count:
                    errors.append(
                        f"链接行号超出文件范围：{target}（文件共 {line_count} 行）"
                    )

    takeaway_count = len(TAKEAWAY_RE.findall(content))
    if effective_mode in {"single", "chapter"}:
        if takeaway_count != 1:
            errors.append(
                f"{effective_mode} 模式应恰好有 1 个“一句话记住”，实际为 {takeaway_count} 个"
            )
        meaningful = [line.strip() for line in content.splitlines() if line.strip()]
        if meaningful and not TAKEAWAY_RE.search(meaningful[-1]):
            errors.append("“一句话记住”不是文档最后一个实质性段落")
    elif takeaway_count:
        warnings.append(f"非正文文件包含 {takeaway_count} 个“一句话记住”")

    if source_links + source_locations == 0 and effective_mode in {"single", "chapter"}:
        errors.append("正文没有可识别的源码链接或 path:line 定位")

    headings = [
        match.group(1).strip()
        for match in re.finditer(r"^#{2,3}\s+(.+)$", content, flags=re.MULTILINE)
    ]
    if effective_mode in {"single", "chapter"}:
        if not any("流程" in heading or "一步步" in heading for heading in headings):
            warnings.append("没有识别到主流程或一步步讲解标题")
        if not any("源码" in heading or "代码" in heading for heading in headings):
            warnings.append("没有识别到源码或代码索引标题")
        if "源码基准" not in content:
            warnings.append("没有记录源码基准 commit 或工作区快照")

    return errors, warnings


def run_self_test() -> int:
    root = Path.cwd().resolve()
    virtual_doc = root / "tutorial-validator-self-test.md"
    valid_text = (
        "# Demo\n\n> 源码基准：当前工作区快照\n\n"
        "## 一步步走主流程\n\n"
        "源码见 [validate_tutorial.py](writing-tutorials/scripts/validate_tutorial.py) "
        "中的 `validate`（`writing-tutorials/scripts/validate_tutorial.py:104-207`）。\n\n"
        "## 源码索引\n\n- `validate`\n\n"
        "> 💡 **一句话记住**：校验器同时检查结构、链接和路径安全。\n"
    )
    valid_errors, _ = validate(virtual_doc, root, "single", text=valid_text)
    if valid_errors:
        print("SELF-TEST FAIL: 合法样例被拒绝")
        for item in valid_errors:
            print(f"  - {item}")
        return 1

    invalid_text = "# <TOPIC>\n\n[file](file:///Users/name/project/file.py)\n"
    invalid_errors, _ = validate(
        virtual_doc, root, "single", text=invalid_text
    )
    if len(invalid_errors) < 3:
        print("SELF-TEST FAIL: 非法样例未触发足够错误")
        return 1

    print("SELF-TEST PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tutorial", nargs="?", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mode",
        choices=("auto", "single", "chapter", "appendix"),
        default="auto",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if args.tutorial is None:
        parser.error("tutorial is required unless --self-test is used")

    errors, warnings = validate(args.tutorial, args.repo_root, args.mode)
    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: 0 error(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
