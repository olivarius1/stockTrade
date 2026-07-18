#!/usr/bin/env python3
"""
报告生成入口：直接调用skill目录中的 report_generator.py
支持命令行参数、财务报表自动获取、10年K线回测
"""
import os, sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REAL_SCRIPT = os.path.join(_SCRIPT_DIR, 'report_generator.py')

if __name__ == '__main__':
    sys.argv[0] = _REAL_SCRIPT
    exec(open(_REAL_SCRIPT, encoding='utf-8').read())
