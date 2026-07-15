#!/bin/bash
# 包装脚本：调用工程目录中的实际 batch_build.sh
# Skill 复用工程代码，不重复实现逻辑

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TRAE_DIR="$(dirname "$SKILL_DIR")"
PROJECT_ROOT="$(dirname "$TRAE_DIR")"

REAL_SCRIPT="${PROJECT_ROOT}/backend/scripts/batch_build.sh"

exec bash "$REAL_SCRIPT" "$@"
