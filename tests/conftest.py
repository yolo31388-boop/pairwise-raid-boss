# 测试文件引用了 math 但未导入，这里通过 builtins 提供，不修改测试本体
import builtins
import math

builtins.math = math
