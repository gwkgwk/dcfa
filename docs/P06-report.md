# P06 单 Skill 能力表示正确性验证与阶段一冻结

目的为验证阶段一单快照表示的具体性质。先在提交 5bfc7d6 固定研究设计和人工 oracle，再编写比较器并运行分析器。输入仅含合成说明、静态 Python 片段和模拟工具声明。未读取外部评价集，未运行待分析脚本。被测模块保持 P05 实现提交 1fc4158 的版本。

## 交付及比较方法

- [设计](P06-design.md) 和[人工输入与预期](../tests/fixtures/synthetic/p06-oracle.json)给出 12 个性质用例；S1 额外提供一个保持语义的变体，共 13 个快照。
- [比较器](../tests/unit/test_representation.py)在临时目录经 extract → build_graph 构建结果。M1 另调用 build_index。按主张及非归属边的多重集精确比较，检查能力节点、边方向和确定性；按用例另核对参数、授权、未知原因或原件路径。不符时断言失败。比较器可作为 pytest 测试，也可直接运行以输出逐例 JSON。
- [实际观察](../examples/p06-observations.json)由比较器运行产生；验收使用事前提交的 oracle。[覆盖矩阵](P06-coverage.md)逐例列出预期、实测、论文依据及项目扩展。

12 项比较均符合事前预期，包括两个预期的表示缺口。D2 的源码存在跨语句值流，C1 的源码具有分支条件；当前图只保留相应的调用与局部操作数。这两项均列为无法表示。C2 能保存授权声明，但不能证明运行时执行了授权检查。S1 比较语义投影，证据坐标及字节哈希允许随编辑变化；本测试没有建立跨版本身份。

## 验收命令

| 命令 | 本次结果 |
|---|---|
| python -m pytest -q tests/unit/test_representation.py | 12 passed |
| python tests/unit/test_representation.py | 输出 12 组实际结果，覆盖 13 个独立快照 |
| python -m pytest -q（Windows Python 3.10.9 和 3.14.0a5） | 两个环境各 91 passed，含前置回归 |
| ruff check . / ruff format --check . | 均通过 |

## 冻结范围与局限

本地注释标签 phase-one-v1.0.0 标记本报告、预注册 oracle、观察记录、测试和阶段一分析器的共同提交。可通过 git rev-parse phase-one-v1.0.0^{} 查得所指提交。接口版本为 SCS p03.2、图 p04.1、证据索引 p05.1。复核旧结果时应使用该标签的完整检出。

自然语言限于已定义文法；Python 调用的动态分派、一般条件、跨语句依赖与未绑定工具仍受限。原件验证只针对当前快照。这里的合成验证不估计真实生态召回率、误报率或恶意更新检测性能。阶段一工程交付冻结，等待人工审核。
