#!/usr/bin/env python3
"""以非覆盖方式初始化 Constellate Wiki。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


DIRECTORIES = (
    "concepts",
    "claims",
    "domains",
    "syntheses",
    "ingests",
    "summaries",
)
BASE_FILES = ("schema.md", "index.md", "log.md")
EXPECTED = tuple(
    [*(f"wiki/{name}" for name in BASE_FILES)]
    + [*(f"wiki/{name}/" for name in DIRECTORIES)]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="初始化 Constellate Wiki；已有文件永不覆盖。"
    )
    parser.add_argument(
        "vault",
        nargs="?",
        default=".",
        help="目标 Markdown/Obsidian Vault，默认当前目录。",
    )
    parser.add_argument(
        "--add-missing",
        action="store_true",
        help="仅为已存在的 wiki 补充已批准的缺失项，仍不覆盖已有内容。",
    )
    parser.add_argument(
        "--only",
        help=(
            "配合 --add-missing 使用，以逗号分隔具体缺失项，"
            "如 schema.md,claims；省略表示补充全部缺失项。"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 输出结果，便于 Agent 解析。",
    )
    return parser.parse_args()


def emit(result: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"状态：{result['status']}")
    print(f"Vault：{result['vault']}")
    print(f"Wiki：{result['wiki']}")
    for label, key in (
        ("已创建", "created"),
        ("已存在", "existing"),
        ("仍缺失", "missing"),
    ):
        values = result[key]
        if values:
            print(f"{label}：")
            for value in values:
                print(f"  - {value}")
    if result.get("message"):
        print(result["message"])


def normalize_only(raw: str | None) -> set[str] | None:
    if raw is None:
        return None

    aliases = {
        **{name: f"wiki/{name}" for name in BASE_FILES},
        **{name: f"wiki/{name}/" for name in DIRECTORIES},
    }
    selected: set[str] = set()
    unknown: list[str] = []
    for item in raw.split(","):
        value = item.strip().replace("\\", "/").strip("/")
        if value.startswith("wiki/"):
            value = value[5:].strip("/")
        normalized = aliases.get(value)
        if normalized is None:
            unknown.append(item.strip())
        else:
            selected.add(normalized)
    if unknown:
        allowed = ", ".join([*BASE_FILES, *DIRECTORIES])
        raise ValueError(f"--only 包含未知项：{', '.join(unknown)}。允许值：{allowed}")
    if not selected:
        raise ValueError("--only 至少需要一个具体项。")
    return selected


def main() -> int:
    args = parse_args()
    try:
        selected = normalize_only(args.only)
    except ValueError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1

    if selected is not None and not args.add_missing:
        print("错误：--only 只能与 --add-missing 一起使用。", file=sys.stderr)
        return 1

    vault = Path(args.vault).expanduser().resolve()
    if not vault.exists() or not vault.is_dir():
        print(f"错误：Vault 不存在或不是目录：{vault}", file=sys.stderr)
        return 1

    wiki = vault / "wiki"
    if wiki.is_symlink():
        print(f"错误：拒绝在符号链接 wiki 上初始化：{wiki}", file=sys.stderr)
        return 1
    if wiki.exists() and not wiki.is_dir():
        print(f"错误：目标 wiki 路径已存在但不是目录：{wiki}", file=sys.stderr)
        return 1

    existed_before = wiki.exists()
    if not existed_before and selected is not None:
        print("错误：全新初始化不接受 --only；请创建完整基础结构。", file=sys.stderr)
        return 1

    assets = Path(__file__).resolve().parent.parent / "assets" / "wiki"
    for name in BASE_FILES:
        template = assets / name
        if not template.is_file():
            print(f"错误：缺少初始化资产：{template}", file=sys.stderr)
            return 1

    existing: list[str] = []
    missing: list[str] = []
    for relative in EXPECTED:
        target = vault / relative.rstrip("/")
        (existing if target.exists() else missing).append(relative)

    if existed_before and missing and not args.add_missing:
        emit(
            {
                "status": "needs-confirmation",
                "vault": str(vault),
                "wiki": str(wiki),
                "created": [],
                "existing": existing,
                "missing": missing,
                "message": (
                    "wiki 已存在；未写入。确认全部缺失项后使用 --add-missing，"
                    "只批准部分时同时使用 --only。"
                ),
            },
            args.json,
        )
        return 0

    approved = set(missing) if selected is None else set(missing) & selected
    created: list[str] = []
    wiki.mkdir(exist_ok=True)

    for name in DIRECTORIES:
        relative = f"wiki/{name}/"
        directory = wiki / name
        if relative in approved and not directory.exists():
            directory.mkdir()
            created.append(relative)

    for name in BASE_FILES:
        relative = f"wiki/{name}"
        target = wiki / name
        if relative in approved and not target.exists():
            shutil.copyfile(assets / name, target)
            created.append(relative)

    remaining = [item for item in missing if item not in created]
    existing_after = [item for item in EXPECTED if item not in created and item not in remaining]
    if not existed_before:
        status = "initialized"
    elif remaining:
        status = "partial"
    else:
        status = "completed"

    message = "初始化完成；没有覆盖任何已有文件。"
    if remaining:
        message = "已补充获批项；未批准或未选择的缺失项保持不变。"
    emit(
        {
            "status": status,
            "vault": str(vault),
            "wiki": str(wiki),
            "created": created,
            "existing": existing_after,
            "missing": remaining,
            "message": message,
        },
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
