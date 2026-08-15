#!/bin/bash
set -e

SKILL_NAME="writing-tutorials"
# Auto-detect Agent skill directory by common conventions; fallback to default
if [ -n "$SKILL_INSTALL_ROOT" ]; then
    SKILL_ROOT="$SKILL_INSTALL_ROOT"
elif [ -n "$CODEX_HOME" ]; then
    SKILL_ROOT="$CODEX_HOME/skills"
elif [ -d "$HOME/.codex" ] || [ -d "$HOME/.codex/skills" ]; then
    SKILL_ROOT="$HOME/.codex/skills"
elif [ -d "$HOME/._agent-cn/skills" ]; then
    SKILL_ROOT="$HOME/._agent-cn/skills"
elif [ -d "$HOME/.trae-cn/skills" ]; then
    SKILL_ROOT="$HOME/.trae-cn/skills"
elif [ -d "$HOME/.claude/skills" ]; then
    SKILL_ROOT="$HOME/.claude/skills"
else
    SKILL_ROOT="$HOME/.codex/skills"
fi

TARGET="$SKILL_ROOT/$SKILL_NAME"
SOURCE="$(cd "$(dirname "$0")" && pwd)"

if [ -L "$TARGET" ]; then
    CURRENT_SOURCE="$(readlink "$TARGET")"
    if [ "$CURRENT_SOURCE" = "$SOURCE" ]; then
        echo "已经安装：$TARGET → $SOURCE"
        exit 0
    fi
    echo "目标位置已有其他 symlink：$TARGET → $CURRENT_SOURCE"
    echo "为避免覆盖，请先运行 uninstall.sh 或手动确认目标。"
    exit 1
elif [ -e "$TARGET" ]; then
    echo "目标位置已有真实文件或目录：$TARGET"
    echo "安装脚本不会覆盖它，请选择其他 SKILL_INSTALL_ROOT。"
    exit 1
fi

mkdir -p "$SKILL_ROOT"
ln -s "$SOURCE" "$TARGET"

echo "✅ 已 symlink：$TARGET → $SOURCE"
echo "触发方式：Use Skill: $SKILL_NAME"
echo "自定义安装位置：SKILL_INSTALL_ROOT=<path> ./install.sh"
