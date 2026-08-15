#!/usr/bin/env python3
'''回归测试 Constellate 的初始化与 lint 脚本。'''

from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
import unittest
import uuid
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
INIT = SKILL_DIR / 'scripts' / 'init_wiki.py'
LINT = SKILL_DIR / 'scripts' / 'lint_wiki.py'
MIGRATE_SOURCES = SKILL_DIR / 'scripts' / 'migrate_sources.py'


class ScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.test_root = SKILL_DIR / f'.constellate-test-{uuid.uuid4().hex}'
        self.vault = self.test_root / 'vault'
        self.vault.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_root)

    def run_script(self, script: Path, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ['python', str(script), *(str(arg) for arg in args)],
            cwd=SKILL_DIR,
            text=True,
            encoding='utf-8',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            capture_output=True,
            check=False,
        )

    def init(self) -> None:
        result = self.run_script(INIT, self.vault, '--json')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def write(self, relative: str, content: str) -> None:
        path = self.vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding='utf-8')

    def make_valid_graph(self) -> None:
        self.init()
        self.write('notes/source.md', '# 原始来源\n')
        ingest = '../ingests/2026-08-05-示例.md'
        common = '''
            tags:
              - 测试
            created: 2026-08-05
            updated: 2026-08-05
            sources:
              - "[[notes/source.md]]"
        '''
        self.write('wiki/concepts/概念A.md', f'''
            ---
            type: concept
            {common.strip()}
            ---
            # 概念A
            ## 定义
            A 的定义。
            ## 边界
            A 的边界。
            ## 语义关系
            - **supports** → [主张B](../claims/主张B.md)：A 为 B 提供直接依据。
            - **part-of** → [领域C](../domains/领域C.md)：A 是 C 的核心组成。
            ## 依据与来源
            来源记录了 A。
            ## 不确定性
            暂无。
            ## 演化记录
            - [示例 ingest]({ingest})：创建本页。
        ''')
        self.write('wiki/claims/主张B.md', f'''
            ---
            type: claim
            {common.strip()}
            state: supported
            origin: source
            ---
            # 主张B
            ## 主张
            B 成立。
            ## 含义与适用范围
            仅适用于测试。
            ## 支持证据
            来源支持 B。
            ## 质疑与反例
            暂无。
            ## 语义关系
            - **depends-on** → [概念A](../concepts/概念A.md)：B 以 A 为必要前提。
            - **part-of** → [领域C](../domains/领域C.md)：B 属于 C 的判断集合。
            ## 当前状态
            现有证据支持。
            ## 不确定性
            暂无。
            ## 演化记录
            - [示例 ingest]({ingest})：创建本页。
        ''')
        self.write('wiki/domains/领域C.md', f'''
            ---
            type: domain
            {common.strip()}
            ---
            # 领域C
            ## 范围
            测试范围。
            ## 知识地图
            由 A 与 B 构成。
            ## 核心问题
            A 如何支持 B？
            ## 主要页面
            A 与 B。
            ## 语义关系
            - **organizes** → [概念A](../concepts/概念A.md)：C 使用 A 组织概念入口。
            - **organizes** → [主张B](../claims/主张B.md)：C 使用 B 组织主张入口。
            ## 依据与来源
            来源覆盖该范围。
            ## 知识缺口
            暂无。
            ## 演化记录
            - [示例 ingest]({ingest})：创建本页。
        ''')
        self.write('wiki/ingests/2026-08-05-示例.md', '''
            ---
            type: ingest
            status: completed
            review: accepted
            created: 2026-08-05T12:00:00+08:00
            sources:
              - "[[notes/source.md]]"
            outputs:
              - wiki/concepts/概念A.md
              - wiki/claims/主张B.md
              - wiki/domains/领域C.md
            ---
            # 示例 ingest
            ## 结果摘要
            已创建三页。
            ## 输入来源
            一篇笔记。
            ## 各来源关键点
            A、B 与 C。
            ## 拟议连接及依据
            六条语义边。
            ## 接受、调整与放弃
            全部接受。
            ## 用户纠正
            无。
            ## 实际改动
            三个核心页。
            ## 矛盾、不确定性与限制
            无。
            ## 外部来源
            无。
            ## 检查
            已运行 lint。
        ''')
        self.write('wiki/index.md', '''
            # Wiki 索引
            ## Domains
            - [领域C](domains/领域C.md) — 测试领域。
            ## Concepts
            - [概念A](concepts/概念A.md) — 测试概念。
            ## Claims
            - [主张B](claims/主张B.md) — 测试主张；状态：supported。
            ## Syntheses
            ## 其他入口
            - [演化日志](log.md)
            - [Ingest 记录](ingests/) — 操作记录。
            - [来源摘要](summaries/) — 来源摘要。
        ''')
        self.write('wiki/log.md', '''
            # Wiki 演化日志
            ## [2026-08-05 12:00] ingest | 示例
            创建三页。
        ''')

    def lint_json(self, *args: object) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = self.run_script(LINT, self.vault, *args, '--json')
        return result, json.loads(result.stdout)

    def test_init_is_non_overwriting_and_lints_empty_wiki(self) -> None:
        self.init()
        lint_result, lint_report = self.lint_json()
        self.assertEqual(lint_result.returncode, 0, lint_result.stderr or lint_result.stdout)
        self.assertEqual(lint_report['graph']['nodes'], 0)
        schema = self.vault / 'wiki' / 'schema.md'
        self.assertIn('## 内容充分性', schema.read_text(encoding='utf-8'))
        schema.write_text('sentinel', encoding='utf-8')
        shutil.rmtree(self.vault / 'wiki' / 'claims')
        report = self.run_script(INIT, self.vault, '--json')
        self.assertEqual(json.loads(report.stdout)['status'], 'needs-confirmation')
        repaired = self.run_script(INIT, self.vault, '--add-missing', '--only', 'claims', '--json')
        self.assertEqual(repaired.returncode, 0, repaired.stderr)
        self.assertEqual(schema.read_text(encoding='utf-8'), 'sentinel')
        self.assertTrue((self.vault / 'wiki' / 'claims').is_dir())

    def test_valid_semantic_graph_passes(self) -> None:
        self.make_valid_graph()
        result, report = self.lint_json()
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(report['errors'], 0)
        self.assertEqual(report['graph'], {'nodes': 3, 'edges': 6, 'components': 1, 'scoped_nodes': 3})

    def test_thin_page_triggers_content_warning_without_structural_failure(self) -> None:
        self.make_valid_graph()
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        thin = [issue for issue in report['issues'] if issue['code'] == 'content-thin']
        self.assertEqual(len(thin), 1)
        self.assertIn('机械预警线 1200', thin[0]['message'])

    def test_local_schema_can_override_content_floor(self) -> None:
        self.make_valid_graph()
        schema = self.vault / 'wiki' / 'schema.md'
        text = schema.read_text(encoding='utf-8')
        text = text.replace('| `concept` | 1200 |', '| `concept` | 1 |')
        schema.write_text(text, encoding='utf-8')
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertNotIn('content-thin', {issue['code'] for issue in report['issues']})

    def test_unknown_relation_type_is_reported_in_scope(self) -> None:
        self.make_valid_graph()
        page = self.vault / 'wiki' / 'concepts' / '概念A.md'
        page.write_text(page.read_text(encoding='utf-8').replace('**supports**', '**related-to**'), encoding='utf-8')
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 1)
        self.assertIn('relation-type', {issue['code'] for issue in report['issues']})

    def test_page_with_only_incoming_edges_is_not_a_graph_error(self) -> None:
        self.make_valid_graph()
        page = self.vault / 'wiki' / 'concepts' / '概念A.md'
        text = page.read_text(encoding='utf-8')
        text = text.replace(
            '- **supports** → [主张B](../claims/主张B.md)：A 为 B 提供直接依据。\n', ''
        ).replace(
            '- **part-of** → [领域C](../domains/领域C.md)：A 是 C 的核心组成。\n', ''
        )
        page.write_text(text, encoding='utf-8')
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        codes = {issue['code'] for issue in report['issues']}
        self.assertNotIn('graph-outdegree', codes)
        self.assertNotIn('graph-min-neighbors', codes)
        self.assertNotIn('graph-isolated', codes)

    def test_one_real_neighbor_is_not_a_graph_error(self) -> None:
        self.make_valid_graph()
        concept = self.vault / 'wiki' / 'concepts' / '概念A.md'
        concept.write_text(
            concept.read_text(encoding='utf-8').replace(
                '- **part-of** → [领域C](../domains/领域C.md)：A 是 C 的核心组成。\n', ''
            ),
            encoding='utf-8',
        )
        domain = self.vault / 'wiki' / 'domains' / '领域C.md'
        domain.write_text(
            domain.read_text(encoding='utf-8').replace(
                '- **organizes** → [概念A](../concepts/概念A.md)：C 使用 A 组织概念入口。\n', ''
            ),
            encoding='utf-8',
        )
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        codes = {issue['code'] for issue in report['issues']}
        self.assertNotIn('graph-min-neighbors', codes)
        self.assertNotIn('graph-isolated', codes)

    def test_legacy_source_path_remains_readable_with_migration_warning(self) -> None:
        self.make_valid_graph()
        page = self.vault / 'wiki' / 'concepts' / '概念A.md'
        text = page.read_text(encoding='utf-8').replace(
            '"[[notes/source.md]]"', 'notes/source.md', 1
        )
        page.write_text(text, encoding='utf-8')
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(report['errors'], 0)
        self.assertIn('source-legacy-path', {issue['code'] for issue in report['issues']})

    def test_source_migration_previews_applies_and_is_idempotent(self) -> None:
        self.make_valid_graph()
        concept = self.vault / 'wiki' / 'concepts' / '概念A.md'
        concept.write_text(
            concept.read_text(encoding='utf-8').replace(
                '"[[notes/source.md]]"', 'notes/source.md', 1
            ),
            encoding='utf-8',
        )
        ingest = self.vault / 'wiki' / 'ingests' / '2026-08-05-示例.md'
        ingest.write_text(
            ingest.read_text(encoding='utf-8').replace(
                '"[[notes/source.md]]"', '"notes/source.md"', 1
            ),
            encoding='utf-8',
        )

        preview = self.run_script(MIGRATE_SOURCES, self.vault, '--json')
        self.assertEqual(preview.returncode, 0, preview.stderr or preview.stdout)
        preview_report = json.loads(preview.stdout)
        self.assertEqual(preview_report['status'], 'preview')
        self.assertEqual(preview_report['change_count'], 2)
        self.assertFalse(preview_report['applied'])
        self.assertIn('notes/source.md', concept.read_text(encoding='utf-8'))

        applied = self.run_script(MIGRATE_SOURCES, self.vault, '--apply', '--json')
        self.assertEqual(applied.returncode, 0, applied.stderr or applied.stdout)
        applied_report = json.loads(applied.stdout)
        self.assertEqual(applied_report['status'], 'migrated')
        self.assertTrue(applied_report['applied'])
        self.assertIn('"[[notes/source.md]]"', concept.read_text(encoding='utf-8'))
        self.assertIn('"[[notes/source.md]]"', ingest.read_text(encoding='utf-8'))

        lint_result, lint_report = self.lint_json()
        self.assertEqual(lint_result.returncode, 0, lint_result.stderr or lint_result.stdout)
        self.assertNotIn(
            'source-legacy-path', {issue['code'] for issue in lint_report['issues']}
        )
        repeated = self.run_script(MIGRATE_SOURCES, self.vault, '--apply', '--json')
        self.assertEqual(json.loads(repeated.stdout)['status'], 'no-changes')

    def test_source_migration_is_atomic_when_a_legacy_target_is_invalid(self) -> None:
        self.make_valid_graph()
        concept = self.vault / 'wiki' / 'concepts' / '概念A.md'
        concept.write_text(
            concept.read_text(encoding='utf-8').replace(
                '"[[notes/source.md]]"', 'notes/source.md', 1
            ),
            encoding='utf-8',
        )
        claim = self.vault / 'wiki' / 'claims' / '主张B.md'
        claim.write_text(
            claim.read_text(encoding='utf-8').replace(
                '"[[notes/source.md]]"', 'notes/missing.md', 1
            ),
            encoding='utf-8',
        )

        result = self.run_script(MIGRATE_SOURCES, self.vault, '--apply', '--json')
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'blocked')
        self.assertFalse(report['applied'])
        self.assertIn('notes/source.md', concept.read_text(encoding='utf-8'))
        self.assertNotIn('[[notes/source.md]]', concept.read_text(encoding='utf-8'))

    def test_source_migration_scope_preserves_wikilink_alias(self) -> None:
        self.make_valid_graph()
        concept = self.vault / 'wiki' / 'concepts' / '概念A.md'
        concept.write_text(
            concept.read_text(encoding='utf-8').replace(
                '"[[notes/source.md]]"', '[[notes/source.md|原始来源]]', 1
            ),
            encoding='utf-8',
        )
        result = self.run_script(
            MIGRATE_SOURCES, self.vault, '--scope', 'concepts', '--apply', '--json'
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'migrated')
        self.assertEqual(report['change_count'], 1)
        self.assertIn(
            '"[[notes/source.md|原始来源]]"', concept.read_text(encoding='utf-8')
        )

    def test_source_wikilink_must_be_quoted_yaml(self) -> None:
        self.make_valid_graph()
        page = self.vault / 'wiki' / 'concepts' / '概念A.md'
        text = page.read_text(encoding='utf-8').replace(
            '"[[notes/source.md]]"', '[[notes/source.md]]', 1
        )
        page.write_text(text, encoding='utf-8')
        result, report = self.lint_json('--scope', 'concepts')
        self.assertEqual(result.returncode, 1)
        self.assertIn('frontmatter-parse', {issue['code'] for issue in report['issues']})

    def test_cancelled_audit_with_outputs_is_rejected(self) -> None:
        self.make_valid_graph()
        page = self.vault / 'wiki' / 'ingests' / '2026-08-05-示例.md'
        text = page.read_text(encoding='utf-8').replace('status: completed', 'status: cancelled')
        text = text.replace('review: accepted', 'review: rejected')
        page.write_text(text, encoding='utf-8')
        result, report = self.lint_json('--scope', 'ingests')
        self.assertEqual(result.returncode, 1)
        self.assertIn('audit-outputs', {issue['code'] for issue in report['issues']})


if __name__ == '__main__':
    unittest.main()
