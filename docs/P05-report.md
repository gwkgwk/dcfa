# P05 原始证据映射验收

实现前设计为 3e7066e。研究问题是给定单一静态快照时，每条能力或图关系的依据能否回到实际存在的材料。依据为 KnotScryer §III-B 的逐主张来源和 P04 的证据指针。精确字节哈希、整文件上下文重放、AST 出现位置和双向索引均为本项目扩展。[设计契约](P05-design.md)

## 交付与接口

- src/dcfa/evidence.py 的 build_index(graph, root, binding_file=None) 校验图并生成 p05.1 索引。src/dcfa/cli.py 提供 evidence 子命令。返回 0 表示全部目标可追溯，1 表示合法索引含缺证，2 表示输入或契约错误。
- src/dcfa/skill_reader.py 向可选观察者传递同一次有界读取的原始字节；src/dcfa/scs.py 在静态提取接受调用主张时提供对应 AST 节点。原 P03、P04 入口继续使用相同的提取逻辑。
- tests/unit/test_evidence.py 为独立回归。examples/evidence.json 是交付索引，可从已提交图和合成快照逐字段重建。

```text
dcfa evidence examples/graph.json tests/fixtures/synthetic/scs-demo
```

可选 --bindings 指向调用方提供的普通 JSON 原件。外部绑定源以 analyst 命名空间下的相对文件名定位，Skill 文件使用 skill 命名空间。两者分别哈希。缺少原件或原件与绑定表不一致时，受影响目标保留缺证。绑定内容格式非法时，命令报输入错误。

## 使用索引

从 by_file 查相对路径，取 capabilities，再用 by_capability 查 nodes／edges。直接归属的文件与外部声明也列在文件索引中。反查使用 by_target.nodes 的图节点 ID 或 by_target.edges 的 /edges/i，然后按 origins 取具体验证证据。单独查 SCS 使用 by_target.capabilities。每条边保留 P04 原始指针、规则键、确定性及全部必要来源；edge_rules 给出规则解释。证据状态分为 verified、partial 和 missing，未验证坐标与实际 witness 分开保存。

例如，样例 /edges/19 是 reads 的可能边。其两端主张 /scs/ports/2 与 /scs/operations/0 都可反查到 SKILL.md 第 17 行。它们描述同一行的两个语义角色，不能当作两个独立观察。scripts/format.py 的调用点可定位至第 2 行、UTF-8 字节列 [11,24)，对应 value.strip()。文件 SHA-256 为 92c1fc270f99ffc096f3bdda44e5ab4634f468e4aac18ef2cd98beffd77bf931。

## 验证

| 命令 | 实际结果 |
|---|---|
| python -m pytest -q tests/unit/test_evidence.py | 12 passed |
| python -m pytest -q，Windows Python 3.10.9 | 79 passed |
| python -m pytest -q，Windows Python 3.14.0a5 | 79 passed |
| ruff check . / ruff format --check . | 检查与格式通过 |
| 已提交图加原合成 Skill 运行 evidence | 退出 0，3 份文件、10 项能力、17 个节点、21 条边均有可追溯依据 |

测试包含清单顺序颠倒、文件改名、行重排、重复指令、同一行重复 Unicode 调用、UTF-8 BOM 与 CRLF、源码和工具声明双来源、缺少原件、伪造函数／路径／行号、代码围栏上下文改变、硬链接拒绝及产物重建。全程仅作静态处理。

## 边界与验收

样例 mapping_status 为 verified，同时 scs_status 为 partial，runtime_observation 为 none。索引验证证据的当前位置；对于 p03.2 未封存的历史原件，仅凭今天重新计算的 SHA-256 不能证实两个时点的字节完全相同。各位置 ID 仅用于当前图。文件级证据的字节区间表示整个默认流，命名流沿用 P03 的未知诊断；调用实参可通过 P04 细分指针定位到所属调用的 AST 证据，未给每个实参单独计算词法区间。未经判断的语义关系仍在 P04 的 unknowns 中。P05 工程验收项已完成，等待人工审核。
