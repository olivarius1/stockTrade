#!/usr/bin/env python3
"""
包装脚本：调用工程目录中的实际 report_generator.py
Skill 复用工程代码，不重复实现逻辑
"""
import os, sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
_TRAE_DIR = os.path.dirname(_SKILL_DIR)
_PROJECT_ROOT = os.path.dirname(_TRAE_DIR)

_REAL_SCRIPT = os.path.join(_PROJECT_ROOT, 'backend', 'app', 'data', 'report_generator.py')

if __name__ == '__main__':
    sys.argv[0] = _REAL_SCRIPT
    exec(open(_REAL_SCRIPT, encoding='utf-8').read())
