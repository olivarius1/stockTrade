#!/usr/bin/env python3
"""
包装模块：复用工程目录中的 kline_manager.py
Skill 复用工程代码，不重复实现逻辑
"""
import os, sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
_TRAE_DIR = os.path.dirname(_SKILL_DIR)
_PROJECT_ROOT = os.path.dirname(_TRAE_DIR)

_REAL_DIR = os.path.join(_PROJECT_ROOT, 'backend', 'app', 'data')

if _REAL_DIR not in sys.path:
    sys.path.insert(0, _REAL_DIR)

from kline_manager import *
