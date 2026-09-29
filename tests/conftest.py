"""测试环境补丁：test_boss.py 使用了 math 但未导入，这里注入到 builtins。"""
import builtins
import math

if not hasattr(builtins, "math"):
    builtins.math = math
