# P04 单 Skill 内部图验收记录

目的为检验一个快照内部的哪些能力关系可由现有证据恢复。原文依据、扩展理由和形式定义先后提交于 cea7e41 和 9ff6e6d，均早于对应实现。[设计与关系定义](P04-design.md)

## 使用与数据契约

```text
dcfa graph examples/p03-scs.json --format json
dcfa graph examples/p03-scs.json --format dot
```

标准输出分别为完整图和 Graphviz DOT；合法部分图导出成功时退出 0，输入／契约错误退出 1，参数错误退出 2。原 SCS 的状态和诊断位于 graph.scs 内。受控的调用方可用 --bindings FILE 提供 JSON 数组。例如合成静态说明的一项可写作 {"operation":0,"callee":"adapter.process","tool":"mock","basis":"synthetic interface"}。operation 从零计数，指向本次 SCS 的 operations 数组；名称和槽位必须相符。使用者负责核实外部绑定说明。示例交付图没有使用工具绑定。

| 文件／接口 | 输入与输出 |
|---|---|
| src/dcfa/graph.py，build_graph | SCS、可选绑定 → 单根图 dict。材料路径视作文档数据；相同名称不合并 |
| validate_graph | 使用内嵌 SCS 和绑定重新推导闭合投影，拒绝多出、缺失、悬空或改写的节点、边、依据与状态。校验通过表示投影自洽；来源真实性依赖调用方 |
| graph_json / graph_dot | 校验图后导出文本，图节点仅用生成的标识作 DOT 端点，原始文本作为引号标签 |
| src/dcfa/cli.py | 提供 graph 子命令。运行时只使用项目原有依赖 |
| tests/unit/test_graph.py | 合成反例、工具绑定与反绑定、嵌套调用关系与证据不一致、篡改、部分和失败输入、CLI 及工件一致性 |
| examples/graph.json、examples/graph.dot | 用已验收的 examples/p03-scs.json 实际导出 |

## 实际结果

样例包含 17 个节点和 21 条边。16 条 contains 仅表示组成关系；1 条 operand 确认源码调用的接收者表达式。2 条 describes、1 条 reads 和 1 条 produces 均为指令文法支持的可能关系。另有 11 条未知记录，包括 P03 的 4 条诊断。单独声明的持久写入效果没有可定位的施事，不能把两个指令端口接成一条已证实的执行链。此样例没有嵌套调用，result_to_operand 由独立合成测试覆盖。

| 实测命令或操作 | 结果 |
|---|---|
| python -m pytest -q tests/unit/test_graph.py | 14 passed |
| python -m pytest -q，Windows Python 3.10.9 | 67 passed in 1.08s |
| python -m pytest -q，Windows Python 3.14.0a5 | 67 passed in 1.22s |
| ruff check . / ruff format --check . | 检查通过，38 个文件格式通过 |
| Graphviz 16.1.0（Viz.js WASM）读取实际 graph.dot | 成功生成 25,191 字节的 SVG。渲染器仅用于导出验证 |

## 边界与验收

所有 confirmed/static 含义均限于输入的存在或语法结构。graph.runtime_observation 固定为 none；没有任何运行时确认边。部分 SCS 及 Setext 等既有不确定性随图保留。未建立基于同名变量、类型、字段共现或文件名的因果边。跨语句绑定、函数间数据流、隐式通道及工具实际执行仍未知。测试验证证据契约，没有估计实际 Skill 上的精度或召回率。P04 工程交付完成，等待人工审核。
