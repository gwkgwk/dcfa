# P08 程序流适配验收

输入为隔离且不可变的单 Skill 快照目录和精确的 POSIX 相对 Python 入口；调用 analyze(directory, entry) 或 python -m dcfa.program_flow DIRECTORY ENTRY。输出 JSON 的 nodes 记录抽象对象和域，edges 记录 owns 或 data_flow 及源码位置，bindings 记录变量使用、定义与参数绑定，issues 标记读取、解析、动态调用或预算缺口。命令在有诊断时退出 1。节点编号仅在本次分析中有效。

合成测试通过真实文件读取、AST 解释及关系导出验证变量覆写、未使用参数、两次独立调用、跨文件返回、文件读取至外部 API 和动态/语法异常。项目 python -m pytest -q 为 107 passed；ruff check . 通过。新增模块 src/dcfa/program_flow.py、tests/unit/test_program_flow.py 及 P08 设计和本报告。未修改阶段一或 P07 分析器。

该实现是静态、调用点敏感的受限 Python 适配。函数体不捕获全局或闭包变量；文件模型只表示句柄、方法及调用结果，未模拟磁盘内容或写后读。简单导入假设缺少同目录模块文件时属于外部声明，包目录、搜索路径、安装状态与运行时覆盖不在解析模型内。外部结果保守依赖全部实参和被调对象。分析只覆盖显式入口，不自动证明其他脚本不可达。控制流、堆属性更新、通用 Python 模块加载和其他语言没有等价于原论文的精度保证。结果用于程序流检查，完整跨域闭包与跨版本判定尚未验收。本阶段提交人工审核。

## 审查修复后的运行契约

以修订后的 P08 设计为准。外部导入显式保留根节点与解析假设。文件路径到 read 结果再到外部调用结果具有可能数据依赖；此路径不证明文件内容、磁盘状态或真实调用。额外输出 entry_analysis、unvisited_functions 以及模块根的 resolution。函数和导入别名的定义位置也进入 bindings。历史 107 项为修复前计数，本轮回归详见 [P08 审查响应](../reviews/P08_review_response.md)。
