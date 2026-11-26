# P03 第二轮独立审查报告

结论：**CONDITIONAL PASS**。第一轮的 16 项代码修复成立，包括对 P03-4 的部分接受。当前实现可以作为下一阶段的接口基础。进入 P04 之前，必须先改正 `docs/P03-report.md`：它仍记录修复前的 30 项测试和 3 条诊断，与现在的 p03.2 输出不符。

本轮没有新的 Critical 或算法级 Major。总分 87。

## 1. 审查范围

| 项 | 值 |
|---|---|
| 第一轮基线 | `5157a4bf8a7d1f204f6e4d51eb303ee7095b34dc` |
| 契约修订 | `589bc429d09c21d3c915c640e448245cf84265c5`，只改 `docs/P03-design.md` |
| 实现与反例 | `986aa6123e3cebe4d691c180a3e63809f63fec3d` |
| 审查对象 | `da4ff579f900e37b5f344d330da026a81abfc547` |
| 第一轮报告 | `reviews/P03_independent_review.md` |
| 报告摘要 | SHA-256 `18cc836a1ee672d43aa7dd36e4e32b734a6c05b72818a26230baaffd2b035524`，与回应文件所载摘要一致 |

回应文件只用来对照开发者的判定，不作为证据。证据来自当前源码、旧测试、新增反例，以及本轮在临时目录中的独立探针。

本环境复核了 Windows 上的 Python 3.14.0a5。Python 3.10.9 的 53 项通过、以及 wheel 归档内容，本轮没有重跑，不计为失败，也不算已核实。文件符号链接仍因权限无法创建。

## 2. 十六项复核

| 项 | 第一轮 | 本轮判定 | 核实结果 |
|---|---|---|---|
| P03-1 标题漏提取 | Major | 已修复 | 先去掉 1–6 级 ATX 标记再匹配。`# Send command from workspace to external.` 与正文传输句同时成为主张，状态可以是 `complete`，片段保留原标题行 |
| P03-2 缩进误提取 | Major | 已修复 | 四格空格和制表符进入 `embedded_example`，不产生主张。三格缩进仍按正文提取，符合 CommonMark 对代码块的四格门槛 |
| P03-3 无效声明置信度 1.0 | Major | 已修复 | `input: [Text]`、空映射和空标量不再产生端口。没有类型就只有诊断 |
| P03-4 传输起点写成 trust_origin 的 null | Major，部分接受 | 接受该部分接受 | 修订契约把传输起点和数据信任来源分开。`from workspace` 写入 `transfer_source`，没有来源证据时 `trust_origin` 仍为 null；显式 YAML `ThirdParty` 仍保留。这满足第一轮给出的另一条验收路径，不要求把起点复制进 `trust_origin` |
| P03-5 条目上限误报文档缺失 | Major | 已修复 | 257 项根目录不再出现 `required_document_unavailable`。文档已解析、子目录再超限时，状态是 `partial_read`，已提取端口保留 |
| P03-6 备用数据流无诊断 | Major | 已修复 | `FindFirstStreamW` 只查流名。普通新文件不会被误报。隐藏流使状态变为 `partial`，流内容不进入 JSON |
| P03-7 测试不能发现上述问题 | Major，部分接受 | 已修复 | 新增反例覆盖上述行为；`test_golden` 比较 `examples/p03-scs.json`。旧断言未改，在新契约下不再与 `null` 的定义冲突 |
| P03-8 默认安装导入崩溃 | Major | 已修复 | 干净虚拟环境执行 `scripts/install_dev.py` 后，PyYAML 6.0.4 的 `__with_libyaml__` 为 False。随后的 `pip install -e .[dev]` 没有换回二进制轮。pytest 为 53 passed |
| P03-9 调用与暴露动作同名 | Major，部分接受 | 已修复 | `kind` 区分 `call_expression` 与 `instruction_action`，并与 `evidence.method` 绑定。单个 `def render` 没有被提升成入口。这个保守选择是对的 |
| P03-10 边界额外键无诊断 | Minor | 已修复 | 额外键按 YAML 键行定位。独立 `.yml` 的第 4 行也能定位，不依赖 frontmatter 偏移 |
| P03-11 未闭合围栏 | Minor | 已修复 | 闭合后恢复正文；未闭合时在开栏行记录 `unclosed_fence`，栏内句子不提取 |
| P03-12 类型大小写 | Minor | 已修复 | `tEXt` 规范为 `Text`。词表外的 `Widget` 保留原文并产生 `unknown_data_type`，状态不是 `complete` |
| P03-13 状态折叠 | Minor，部分接受 | 已修复 | 文档已取得且存在 `read_failure` 时为 `partial_read`；其他诊断为 `partial`；文档未取得为 `failed`。退出码 1 仍只表示工程不完整 |
| P03-14 调用顺序 | Suggestion，部分接受 | 已修复 | 按起始行、列和结束位置排序。同一行的 `a(b())` 得到外层 `a` 再内层 `b` |
| P03-15 角色与处理状态 | Suggestion，部分接受 | 已修复 | `processing` 独立于 `role`。超限文档为 `unread`，仅登记文件为 `inventory_only`，送入解释器的文件为 `processed` |
| P03-16 校验器与异常出口 | Suggestion | 已修复 | 校验器按进程缓存。注入空摘要时 CLI 返回退出码 1 和 `{"status":"failed","error":"scs_contract_failure"}` |

设计提交 `589bc42` 早于实现提交 `986aa61`，且只包含修订契约。旧测试文件不在实现差异中。`test_transfer_instruction` 仍断言 `trust_origin is None`；在 p03.2 中这表示没有数据信任来源证据，传输起点另存于 `transfer_source`。

## 3. 本轮独立探针

预期在调用 `extract` 之前写定。43 项全部符合预期。决定性结果如下。

| 探针 | 预期 | 实际 |
|---|---|---|
| 单条授权传输句 | `complete`，`transfer_source=local`，`trust_origin=null` | 符合。普通文件的流枚举返回 False，没有误伤 `complete` |
| 标题中的 Command 加正文 Text | `complete`，两枚端口，片段为原标题行 | 符合 |
| 四格缩进传输句 | 无主张 | 开发者测试已覆盖，本轮不重复失败 |
| 三格缩进传输句 | 仍提取为 Command | 符合 |
| 非文法标题 `# Overview` | `partial`，第 1 行有诊断，正文端口保留 | 符合 |
| `input: [Text]` | 无端口 | 符合 |
| 超长 `SKILL.md` | `failed`，`byte_limit`，`processing=unread` | 符合，不再报成文档不存在 |
| 先读到文档，子目录再超过 256 项 | `partial_read`，端口保留，无文档缺失诊断 | 符合 |
| 隐藏流中的另一条传输句 | 不是 `complete`，JSON 不含该句 | 符合 |
| `a(b())` | 调用顺序 `a`、`b` | 符合 |
| 干净 venv 运行 `scripts/install_dev.py` 后 pytest | 纯 Python YAML，测试通过 | `libyaml False`，53 passed in 1.04s |

同一环境里，修复前使用的虚拟环境直接运行当前套件也是 `53 passed in 0.80s`。`ruff check .` 与 `ruff format --check .` 通过。

## 4. 仍存在的问题

### R2-1　Major　阶段验收记录仍是修复前的事实

- 位置：`docs/P03-report.md:27-37`
- 描述：记录仍写 Python 3.10.9 与 3.14.0a5 均为 30 passed，示例有 3 条未知诊断，并且没有 p03.2、`partial_read`、`transfer_source` 和 `scripts/install_dev.py`。
- 根因：实现和样例已更新，阶段验收记录没有随 `986aa61` 修改。回应文件写了 53 项和 4 条诊断，但 `docs/P03-report.md` 仍是项目声明的验收记录。
- 影响：后续读者会引用错误的测试次数和错误的样例结构。当前样例实际有 4 条诊断：标题行 16、未解释正文行 19、运行时未知和 `inventory_only`。
- 证据：报告第 29–37 行；`examples/p03-scs.json:175-199`；本轮 pytest 为 53 passed。
- 修复：按当前命令重写实测表、诊断条数、状态枚举和安装入口。不要把回应文件里的数字直接抄入而不再运行。
- 验收：报告中的测试次数、退出状态、诊断条数和版本号与 `da4ff57` 的实际输出一致，并且写明退出码 1 不用于风险统计。

### R2-2　Minor　Setext 标题的第一行仍会成为主张

- 位置：`src/dcfa/scs.py:205-253`
- 描述：`Send command from workspace to external.` 后接 `====` 时，第一行被提取为 Command。下划线本身是 `uninterpreted_instruction`，所以状态不是 `complete`。
- 根因：修订契约只移除 ATX 标记，没有向前看一行下划线。
- 影响：Setext 标题会留下一条真实传输主张。诊断仍在，不会伪装成封闭的 `complete`。
- 证据：本轮 `setext` 探针得到端口 `Command`，且状态不是 `complete`。
- 修复：可在后续文法修订中把 Setext 标题整组标为未解释。不必在进入 P04 设计前完成。
- 验收：该两行文件不产生传输主张，或者设计明确把 Setext 排除在 ATX 规则之外并保留诊断。

以下现象符合已修订契约，不列为缺陷：非文法标题会使状态保持 `partial`；词表外类型以原文进入端口并带诊断；四格及以上的列表行进入示例诊断；token 超限的文件仍标为 `processed`，同时有 `python_token_limit`。下一阶段不得把 `partial`、`partial_read` 或退出码 1 当作风险标签。

## 5. 评分

| 评价维度 | 第一轮 | 本轮 | 依据 |
|---|---:|---:|---|
| 原始任务完成度 | 9 | 13 | 有界 SCS 子集已按修订契约闭合第一轮的判定错误。它仍不是论文自然语言启发式的完整复现 |
| 算法正确性 | 13 | 22 | 标题、缩进、无效声明、流枚举、状态和调用顺序已与契约一致。Setext 仍会生成主张 |
| 科研严谨性 | 13 | 17 | 契约先于修复提交，来源字段的区分有论文依据。验收记录没有同步 |
| 软件架构与代码质量 | 8 | 9 | `processing`、`kind` 和 `partial_read` 把先前折叠的状态分开了 |
| 测试有效性 | 7 | 13 | 反例能否决第一轮的错误 `complete`，样例文件被测试引用。本轮 43 项独立探针未发现反例失败 |
| 鲁棒性与安全性 | 3 | 4 | 不执行、不读取命名流、超限原因可追溯。文件符号链接仍未实证 |
| 可复现性 | 3 | 4 | 干净安装和 53 项测试已在 3.14.0a5 复核。3.10.9 与 wheel 本轮未复核 |
| 阶段隔离与接口设计 | 4 | 5 | 仍无 handoff 或策略搜索。调用表达式不能再通过 schema 冒充指令动作 |
| 合计 | 60 | 87 | 无 Critical。R2-1 未改正前不能 PASS |

## 6. 是否进入下一阶段

算法修复可以接受，现在还不能进入 P04。

条件只有一条：更新 `docs/P03-report.md`，使实测次数、样例诊断、p03.2 字段和安装入口与 `da4ff57` 的实际行为一致。不需要为这 16 项再改提取器。R2-2 可以留到后续文法修订。

P04 若开始，输入应是 p03.2 的主张，并按 `kind` 分开指令动作和调用表达式。`transfer_source` 不是 `trust_origin`。非 `complete` 只表示这个有界提取器没有封闭，不表示发现了恶意更新。
