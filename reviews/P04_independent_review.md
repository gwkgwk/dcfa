# P04 独立代码审查报告

结论：**PASS**。可以进入 P05 的设计。本审查不修改实现，也不启动 P05。

P04 交付的是一张由 p03.2 证据约束的单 Skill 图。指令关系的方向、确定性、锚点隔离和嵌套实参槽，在独立样本上与已提交的设计一致。论文算法 1 第 4 行没有给出逐边规则；当前实现把这一点写成了适配和扩展，没有包装成 KnotScryer 的逐边复现。没有 Critical，也没有阻塞进入 P05 的 Major。

进入 P05 时必须沿用下面的读图约定：位置指针只在一次快照内有效；`possible` 不是运行时确认；图中没有出现的关系族，只表示本阶段没有建立该关系。

## 1. 审查范围与环境

| 项 | 值 |
|---|---|
| 对象 | `ab57ecba4af8691fa19c870adff4f1041254f2a0`，分支 `main` |
| 审查方式 | 只读。未改 `src/`、`tests/`、`examples/`、数据集或标签，未提交 |
| 实现 | `src/dcfa/graph.py`、`src/dcfa/cli.py` 的 `graph` 子命令 |
| 设计与记录 | `docs/P04-design.md`、`docs/P04-report.md` |
| 前置 | `src/dcfa/scs.py`、`docs/P03-design.md`、`docs/P03-report.md`、三份 P03 独立审查 |
| 论文 | 已获取的 KnotScryer HTML（arXiv:2610.32155v1）中 §III-C 与算法 1；对照 `docs/reproduction/knotscryer_scope.md` |
| 环境 | Windows，Python 3.14.0a5。审查用可编辑安装指向当前工作区。`py -0p` 只列出 3.14 |

仓库中没有另一份独立的 P04 任务书。完成度以 `cea7e41`、`9ff6e6d` 提交的设计，以及 `AGENTS.md` 中“验证单 Skill 内部能力流”这一步为准。官方 KnotScryer 程序仍未入库，逐边规则无法对照作者实现。Python 3.10.9 与 Graphviz SVG 的字节数，本环境没有复核。

## 2. Git 分支及 Commit ID

- 分支：`main`
- HEAD：`ab57ecba4af8691fa19c870adff4f1041254f2a0`
- 工作区：审查开始时只有未跟踪的三份 P03 审查报告。`src/` 干净
- 设计提交：`cea7e41`（证据规则），`9ff6e6d`（直接嵌套值流），均早于实现
- 实现提交：`ab57ecb`。新增 `graph.py`、`test_graph.py`、`examples/graph.json`、`examples/graph.dot`、`docs/P04-report.md`，并给 `cli.py` 增加 20 行。同一提交还在设计末尾追加了双星号展开的跳过规则
- 该提交没有修改 `scs.py`、`skill_reader.py` 或 P03 测试

## 3. P04 原始任务及实际实现

设计把本阶段定义为：对一份已校验的 p03.2 快照 S，以及可选的分析者绑定 B，生成 G=(V,E,U)。分析器不打开 S 或 B 里引用的路径。身份是本次 JSON 中的位置指针。`runtime_observation` 固定为 `none`。

`build_graph` 先校验并深拷贝输入，再为文件、端口、效果、操作、上下文和信任边界建点。指令片段用 P03 的 `Material.document` 在同一行上重放；只有重放结果与主张一致、且该锚点恰好有一个动作时，才连接 `reads`、`produces`、`may_cause`、`exposes`、`crosses-boundary`，确定性为 `possible`。调用点的实参和接收者用 `operand` / `static`。显式绑定且名称一致时，才有 `may_invoke` / `possible`。同一单行、调用数量和实参源码都能对上时，直接占据参数槽的内层调用得到 `result_to_operand` / `possible`。对不上则写入 `local_value_flow_unresolved`，不连边。

`validate_graph` 用同一函数重建图，再做规范 JSON 比较。CLI 在导出前校验。合法图退出 0，契约错误退出 1，参数错误退出 2。

本阶段没有版本差分、跨 Skill handoff、策略判定或风险标签。`src/` 中没有这些字样，也没有 TODO 或空函数。

## 4. 原始任务逐项验收表

| 设计要求 | 结论 | 证据 |
|---|---|---|
| `build_graph(S, B)` 返回带 `p04.1`、内嵌 SCS、节点、边、未知和 `runtime_observation=none` 的对象 | COMPLETE | `graph.py` 231–239 行；传输句与样例探针 |
| 位置指针，同名对象不合并 | COMPLETE | 两句相同的 `Accept text.` 得到 2 个输入端口和 2 条 `reads` |
| 指令重放、唯一动作、字段一致才连边 | COMPLETE | 类型被改成 `Command`、同行两个动作、敏感度被改写时都不连边 |
| 输入端口指向动作；动作指向输出、效果、上下文、边界 | COMPLETE | 见第 11 节方向探针 |
| 确定性为可能，证据为两端指针 | COMPLETE | 样例中 `describes`、`reads`、`produces` 的确定性集合只有 `possible` |
| 实参源码表达式为静态操作数 | COMPLETE | `f(g(), x=h())` 的槽号与关键字顺序一致 |
| 点号调用记录接收者表达式 | PARTIAL | 边存在且为 `static`；有空白时标签不是源码片段。见 P04-1 |
| 无绑定不推断工具；绑定须索引、名称、种类一致 | COMPLETE | 错名称、重复绑定、把绑定指到指令动作均抛出 `ValueError` |
| 资源出现不等于被读取 | COMPLETE | 样例资源只有 `resource_usage_unresolved`，没有指向该文件的 `reads` |
| 直接嵌套槽的 `result_to_operand` | COMPLETE | 函数体内缩进的 `f(g())`、`f(g(), x=h())`、既有 `consume(item=make())` 测试 |
| 分行、动态目标、数量或实参不符时只记未知 | COMPLETE | 多行 `f(\n g()\n)` 与 `make().process(x)` 均无结果边，并有 `local_value_flow_unresolved` |
| 双星号父调用跳过结果槽 | COMPLETE | `f(g(), **kw)` 无结果边。该句与实现同一提交写入设计，见 P04-5 |
| 校验是投影自洽，导出前执行 | COMPLETE | 篡改测试 5 项失败于 `ValueError`；记录写明校验不认证来源 |
| CLI 的退出码与两种格式 | COMPLETE | 部分图和失败但合法的 SCS 退出 0；`{}` 退出 1 且 stdout 为空；缺参数退出 2 |
| 不执行技能、不跟随证据路径 | COMPLETE | 含写文件调用的样本没有创建标记文件；伪造但自洽的片段仍能连上 `possible` 边，与设计第 9 行一致 |
| 不建 transforms、sanitizes、跨语句 def-use | COMPLETE | 这些关系不在样例边集合中。图对象没有单独的“本族未建模”记录，见 P04-4 |
| 不提前做差分、handoff 或检测器 | COMPLETE | 实现提交的文件范围和第 7 节 |
| 设计先于代码 | PARTIAL | 主体规则在 `cea7e41` 与 `9ff6e6d`。双星号例外在 `ab57ecb` 与代码同时出现 |

## 5. 参考论文与代码对应关系

论文 §III-C 写明：节点包括 skill、输入端口、输出端口、效果、操作、上下文和信任边界；技能内部的边包括 reads、produces、transforms、exposes、sanitizes、crosses-boundary。算法 1 第 4 行是“把 s、内部节点和技能内部边加入 V、E”。同一节把跨技能边放在四个 handoff 条件之下。已获取正文没有展开每一条内部边怎样从语句恢复。P01 范围说明与这段正文一致。

| 论文或设计对象 | 代码 | 归类 |
|---|---|---|
| 单技能内部的端口、操作、效果、上下文、信任边界节点 | `build_graph` 中按 SCS 分组建点 | Necessary Adaptation。论文节点类别还在；跨技能 handoff 按研究边界排除 |
| reads、produces、exposes、crosses-boundary | 指令重放后的有向边，确定性 `possible` | Original Extension。词汇来自论文；端点方向和“必须重放一致”是本项目规则 |
| transforms、sanitizes | 不建边 | Necessary Adaptation。论文列出了词汇，没有恢复算法；设计明确留为未知 |
| may_cause、describes、contains、operand、may_invoke、result_to_operand | `RELATIONS` 与调用分析 | Original Extension。论文效果节点没有这条 `may_cause`；PROV 只被设计引用为实体和活动分开建模 |
| 算法 1 第 4 行的整步内部建图 | 证据子集，不是作者程序 | 不能标成 Faithful Reproduction。官方源码缺失，论文也没有逐边过程 |
| 式 (1) 的跨技能配对 | 未实现 | 正确的范围排除，不是遗漏 |

没有把关键词共现、同名或同类型写成语义边。前置声明和后文指令即使类型相同也不连接。这一点由 `test_same_type_no_flow` 和独立的 frontmatter 探针共同支持。

## 6. 算法正确性分析

指令边的方向在代码里是确定的：输入端口是 `reads` 的源，其余角色以动作为源。

```224:227:src/dcfa/graph.py
            if kinds[ref] == "input_port":
                edge(ref, "reads", action, "possible")
            else:
                edge(action, RELATIONS[kinds[ref]], ref, "possible")
```

独立样本 `Send text from local to external after explicit authorization.` 得到四条 `possible` 边：动作指向输出端口、效果、上下文和信任边界，没有 `reads`。`Accept text.` 与 `Return code.` 分属两个动作。`- Accept text.` 和 `### Return code ###` 在重放剥去列表标记或 ATX 标题后仍然连到正确方向。

嵌套规则只在整行 AST 调用数、名称和实参源码都与 SCS 记录一致时生效。`f(g(), x=h())` 得到 `g → f/arg0` 和 `h → f/arg1`，槽号按位置参数然后关键字值排列，与 P03 的参数顺序一致。函数体中的 `    f(g())` 在去掉行首空白后仍能对上，边为 `g → f/arg0`。多行调用和 `make().process(x)` 对不上，只有未知、没有结果边。把内层调用改名后，既有测试同样失去结果边。

接收者标签是名称前缀，不是属性值的源码片段：

```189:193:src/dcfa/graph.py
                if "." in label:
                    operands.append(("receiver", label.rsplit(".", 1)[0], ref + "/name"))
                for slot_name, expr, basis in operands:
                    operand = node(ref + "/" + slot_name, "data_expression", expr, basis, ref)
                    edge(operand, "operand", ref, "static")
```

`foo . bar . baz()` 的源码片段是 `foo . bar`，图上的静态标签是 `foo.bar`。样例里的 `value.strip` 没有这种空白，所以验收记录中的那一条接收者边碰巧与源码一致。见 P04-1。

`h(*g())`、`f(a[g()])` 和 `f(g(), **kw)` 都没有结果边。前两者的内层调用不是直接的位置参数或关键字值；后者按设计整段跳过。这三种情况也没有 `local_value_flow_unresolved`。规则对“对不上的行”要求记未知，对“对得上但槽不是直接子节点”没有要求记未知。因此这是范围边界，不是实现偏离设计。下游如果把缺边读成“已经证明没有值流”，会超出这张图能支持的命题。见 P04-3。

`validate_graph` 比较的是 `build_graph` 的不动点。它能发现篡改，不能发现建图函数自身的系统性偏差。设计写的是“校验通过表示投影自洽”。这个表述与代码一致。

失败快照仍可导出：没有 `SKILL.md` 的目录得到 `status=failed`、空边集，CLI 退出 0。设计把非零退出留给无法通过契约的输入。`{}` 退出 1，stdout 为空，错误只进日志。

复杂度由 P03 的条目、长度和标记上限约束。建图本身遍历主张和单行 AST，指针字典的规模随主张数线性增长。同一输入两次调用结果相等，并且不修改调用方对象。

## 7. P03—P04 接口分析

P04 调用 `scs.validate`，拒绝非 p03.2。图内嵌整份 SCS，边的证据是 `/scs/...` 或 `/bindings/...` 指针。`transfer_source` 仍留在端口对象里，没有被改写成 `trust_origin`。`call_expression` 只有在绑定名称完全一致时才连到工具；指令动作不能占用调用槽。

P03 的诊断进入图的未知列表，主体是 `skill`。样例中有 4 条诊断指针。`partial`、`partial_read`、`failed` 原样保留，没有被换成风险标签。Setext 行 `Send text from local to external.` 后接 `====` 时，P03 仍会抽出传输主张，P04 据此连出 `possible` 的 `produces`，状态保持 `partial`。这是前置行为的传播；P04 没有把它提升为 `static`。

`ab57ecb` 没有改 P03 提取器。全量测试中的 `test_scs.py`、`test_p03_review.py`、`test_skill_reader.py` 仍在 67 项之内并通过。

P05 应读取 p04.1，同时保留内嵌的 p03.2。`/scs/ports/0` 这类指针在下一次版本中会随数组位置变化，不能当作跨版本实体标识。绑定是分析者假设。`runtime_observation` 恒为 `none`。

## 8. 科研科学性分析

方法身份与证据相符：论文提供节点类别和内部关系词汇，逐边恢复是项目扩展。实现没有按样本名、路径或攻击字符串分支。测试夹具是合成句和合成调用，断言写的是关系和指针，不是某个外部数据集的标签。

验收记录有两处不能当成已经在本环境证实的实验事实。Python 3.10.9 的 “67 passed in 1.08s”，以及 Graphviz 16.1.0 生成 25,191 字节 SVG，本机没有对应解释器，也没有重跑渲染器。记录还写所有形式定义都早于实现；双星号那一句是与 `graph.py` 同一提交进入设计的。见 P04-5。

通过的测试说明契约在这些合成例上成立。它们没有估计真实 Skill 上的精度或召回，记录自己也这样写了。伪造一段与文法一致的片段仍会得到 `possible` 边，因为图不回读原文件。这是设计已声明的信任前提：输入应来自可信的 P03 流程。

## 9. 软件工程质量评价

`graph.py` 只有建图、校验和两种导出，输入输出明确。异常为 `JsonSchemaException`、`ValueError` 和解析失败后的未知记录，没有把异常吞成空的成功图。CLI 对契约错误返回 1；成功图的 stdout 是 JSON 或 DOT。

实参使用 `ast.get_source_segment`，接收者使用点号前缀，证据指针分别是参数槽和整个 `name`。同一类“语法操作数”有两种粒度。见 P04-1。

DOT 的节点标签经过 JSON 转义。边上的关系名来自固定集合。未知项用注释节点连到主体，主体 `skill` 一定存在。

## 10. 现有测试有效性分析

`tests/unit/test_graph.py` 收集到 14 项，并随全量 67 项通过。它们实际证明了：

- 五种指令关系存在、确定性为 `possible`、每条有两个证据指针
- 前置声明不与后文指令接成 `produces` 或 `may_cause`，`reads` 的源是 `/scs/ports/2`
- 改行号、改数据类型、复制第二个动作后没有 `produces`
- 三个静态操作数；错误或重复绑定被拒绝；正确绑定得到 `possible` 的 `may_invoke`
- 资源不是 `reads` 的源；输入 SCS 与图内嵌副本相等
- 改端点、确定性、证据、删边、改运行时观察都会被校验拒绝
- `consume(item=make())` 的结果边端点是操作 2 到操作 1 的 `arg0`；改名后边消失并出现未知
- 空目录失败图没有边
- `examples/graph.json` 与当前 `build_graph(extract(样例))` 相等

它们没有证明指令边的方向。`test_instruction_roles` 只解构出边，然后检查确定性和证据长度。DOT 测试把命令输出与 `graph_dot(graph)` 比较，两端是同一个导出函数。黄金文件测试证明交付物等于当前函数，不能单独证明函数符合论文。校验测试证明篡改检测，不能证明重建函数本身的语义。星号展开、下标嵌套、标题行和多行调用不在这 14 项里；这些由第 11 节的独立样本覆盖。

既有测试因此不是虚假通过：失败路径会拒绝具体的错误图，嵌套测试检查了真实端点。它们对指令方向和导出文本的约束偏松。见 P04-2。

## 11. 独立测试与反例验证结果

预期先按 P03 文法和 P04 设计写出，再调用 `extract` 与 `build_graph`。样本在系统临时目录，不在仓库中。除接收者标签一项按预期失败外，其余事先写明的产品预期均成立。有一次把顶层 `    f(g())` 当成合法调用，P03 正确地给出 `invalid_python` 且没有调用记录；该输入不符合 Python 语法，不记为产品缺陷。随后改测函数体内的同一调用，结果边存在。

| 编号 | 目的 | 预期 | 实际 | 结果 |
|---|---|---|---|---|
| T01 | 基础方向与样例计数 | 传输句四条出边；样例 17 点、21 边、关系计数 16/1/2/1/1 | 与预期一致；操作数 `static`，三条能力边 `possible` | 通过 |
| T02 | 空快照 | 无 `SKILL.md` 时无边、状态 `failed`、观察值为 `none`；CLI 退出 0 | 一致，stdout 可解析 | 通过 |
| T03 | 非法输入 | `{}` 与错误绑定失败；CLI 对 `{}` 退出 1 且 stdout 为空；缺参数退出 2 | 一致 | 通过 |
| T04 | 最小反例 | 改敏感度后重放不一致，`reads` 消失并记 `instruction_role_unresolved` | 一致 | 通过 |
| T05 | 同文不合并 | 两行 `Accept text.` 为两条 `reads`、两个输入端口 | 2 与 2 | 通过 |
| T06 | 实质变化 | `Accept` 与 `Return` 的动作不同；标题行和列表行仍按方向连接 | `reads` 的目标不是 `produces` 的源；列表与 `### Return code ###` 方向正确 | 通过 |
| T07 | 多层调用 | `f(g(), x=h())` 两个槽；函数体内缩进可连接；多行和动态目标只有未知 | 槽号 `/arg0`、`/arg1`；动态调用无结果边 | 通过 |
| T08 | 信息不足 | 前置声明不连因果边；`*g()`、`a[g()]`、`**kw` 无结果边 | 前置无 `produces`/`may_cause`；三种嵌套都无结果边。后三者同时没有流未知记录 | 通过；边界见 P04-3 |
| T09 | 前置异常 | Setext 保持 `possible` 和 `partial`；顶层非法缩进只保留 `invalid_python` | 一致，没有提升为静态边 | 通过 |
| T10 | 重复运行 | 两次建图相等，且不改调用方 SCS | 规范 JSON 相等 | 通过 |
| T11 | 契约 | 图内嵌原 SCS；失败图仍是 p04.1；工具绑定不能指向指令动作 | 样例测试中 `graph["scs"]==data`；错误绑定抛出 `ValueError` | 通过 |
| T12 | 回归 | P03 与 P04 测试一起通过 | `67 passed in 0.89s` | 通过 |

接收者反例：源码 `foo . bar . baz()`。属性值的源码片段是 `foo . bar`。图中 `data_expression` 标签是 `foo.bar`，`operand` 边的确定性仍是 `static`。

写文件探针：样本脚本包含创建标记文件的调用。`build_graph(extract(...))` 之后标记文件不存在。

## 12. 前置模块回归测试结果

在当前工作区执行 `python -m pytest -q --tb=line`：`67 passed in 0.89s`。收集结果含 `test_scs.py`、`test_p03_review.py`、`test_skill_reader.py`、`test_cli.py` 和 14 项 `test_graph.py`。`ruff check .` 与 `ruff format --check .` 均通过；格式检查报告 39 个文件已格式化。验收记录写的是 38 个文件，数量差不影响“检查通过”这一结论，本审查没有据此单列缺陷。

P03 第三轮允许保留的 Setext 行为仍然存在，并且 P04 只以 `possible` 消费它。文件符号链接仍属于 P03 的未实证项，本轮没有重开。

## 13. 完整缺陷清单

### P04-1　接收者静态标签不是源码片段

- 严重等级：Minor
- 状态：CONFIRMED
- 文件：`src/dcfa/graph.py` 189–193 行
- 描述：点号调用的接收者标签是 `name.rsplit(".", 1)[0]`。实参标签来自源码片段。接收者边的确定性为 `static`。
- 根本原因：接收者没有使用 `Attribute.value` 的 `ast.get_source_segment`。
- 依据：设计要求点号调用另记录接收者表达式，并把操作数标为静态语法事实。论文没有这条接收者规则。
- 影响：`foo . bar . baz()` 的源码是 `foo . bar`，标签是 `foo.bar`。无空白的 `value.strip` 不受影响。不改变边的存在和方向。
- 反例：仅含 `Read text.` 与 `foo . bar . baz()` 的合成快照。
- 修复：接收者标签改为属性值的源码片段，证据指针指向该片段所在的调用证据。
- 验收：上述反例的标签等于 `foo . bar`，边仍是 `operand` / `static`；无空白样本保持原标签。
- 是否阻塞 P05：否

### P04-2　指令边方向没有被既有测试锁住

- 严重等级：Minor
- 状态：CONFIRMED
- 文件：`tests/unit/test_graph.py` 22–29 行；DOT 比较在 105–106 行；黄金文件在 131–137 行
- 描述：指令测试检查关系名、确定性和证据个数。方向由本审查的独立探针证实，不由该测试证实。DOT 与黄金文件比较的是同一实现的再生结果。
- 根本原因：断言停在边的属性，没有写源和目标的角色。
- 依据：设计表规定输入端口指向动作，动作指向其余角色。
- 影响：以后若把 `reads` 方向写反，这 14 项里的指令测试仍可能通过。当前代码方向是对的。
- 修复：为 `Accept` 与 `Send` 各断言一条源、目标、关系和确定性。导出测试至少检查一条已知边的样式，而不只和 `graph_dot` 自比。
- 验收：故意对调 `reads` 的源和目标时，新增断言失败。
- 是否阻塞 P05：否

### P04-3　若干语法值流既无边也无未知记录

- 严重等级：Suggestion
- 状态：CONFIRMED
- 文件：`src/dcfa/graph.py` 72–80 行；设计最后一行
- 描述：`h(*g())`、`f(a[g()])`、`f(g(), **kw)` 没有 `result_to_operand`，也没有 `local_value_flow_unresolved`。
- 根本原因：未知记录只加在整行无法对账时。直接槽规则对得上时，星号、下标和双星号父调用被跳过，返回空配对。
- 依据：设计只承诺直接的位置参数或关键字值，并写明双星号父调用保守跳过。论文没有局部值流规则。
- 影响：缺边表示“本规则未连接”，不表示“已证明没有值流”。当前实现与这条窄规则一致。
- 修复：若后续要让缺边可解释，可为被跳过的父调用增加明确的未知原因，同时保留现有的不连边行为。
- 验收：上述三例仍然没有结果边；若增加未知记录，原因与“对账失败”可区分。
- 是否阻塞 P05：否。P05 不得把缺边当作负证据

### P04-4　未建模关系族没有进入 U

- 严重等级：Suggestion
- 状态：CONFIRMED
- 文件：`src/dcfa/graph.py` 的 `RELATIONS` 与未知列表；`docs/P04-design.md` 第 22 行
- 描述：transforms、sanitizes 和跨语句 def-use 没有边，也没有一条图级未知说明这些关系族未被计算。
- 根本原因：未知列表只收集具体主张上的缺口和 P03 诊断。设计把这些族留在算法范围外。
- 依据：论文列出了 transforms 与 sanitizes，但算法 1 第 4 行没有恢复过程。
- 影响：只遍历 U 的后续分析看不到“该族未评估”。
- 修复：在 p04.1 中增加显式的未建模关系清单，或者由 P05 设计声明缺席的关系族不是观察结果。
- 验收：读者不需要阅读设计散文，就能知道这些关系没有被计算。
- 是否阻塞 P05：否。P05 的设计必须写出这条读图约定

### P04-5　双星号例外与实现同一提交写入设计

- 严重等级：Minor
- 状态：CONFIRMED
- 文件：`docs/P04-report.md` 第 3 行；`docs/P04-design.md` 第 31 行
- 描述：验收记录称形式定义于 `cea7e41` 和 `9ff6e6d`，均早于实现。`git show ab57ecb -- docs/P04-design.md` 显示双星号跳过规则是实现提交新增的一行。
- 根本原因：实现过程中收紧了局部规则，并同时补进设计。
- 依据：阶段要求先有设计再实现。主体规则满足；这一条例外不满足“全部早于实现”。
- 影响：不改变当前跳过行为的可审查性，因为设计和代码现在一致。它削弱“所有形式定义都先冻结”这一句的准确性。
- 修复：在验收记录中写明该句的提交是 `ab57ecb`。
- 验收：记录中的提交号与 `git log` 一致。
- 是否阻塞 P05：否

未列为缺陷的核对项：样例 17 个节点、21 条边、11 条未知与本环境重跑一致；失败图退出 0 符合“合法图可导出”；伪造自洽片段得到 `possible` 边符合设计第 9 行；P03 源文件不在实现提交中。

## 14. 综合评分及评分依据

| 评价维度 | 满分 | 得分 | 依据 |
|---|---:|---:|---|
| 原始任务完成度 | 15 | 14 | 设计中的建图、未知、CLI 和合成反例均已实现并复测。双星号规则没有先于代码冻结，扣 1 分 |
| 算法正确性 | 25 | 22 | 方向、锚点、重放失败、嵌套槽、动态目标和不执行均由独立样本证实。接收者标签与源码片段可偏离；部分语法流没有未知记录 |
| 科研严谨性 | 20 | 18 | 方法身份、范围和“自洽不是来源认证”写得清楚。3.10.9、SVG 字节数和“定义全部早于实现”不能按原句采信 |
| 软件架构与代码质量 | 10 | 9 | 模块边界清楚，导出前校验。接收者与实参的证据粒度不一致 |
| 测试有效性 | 15 | 12 | 14 项测试包含真实反例和嵌套端点。指令方向、DOT 和黄金文件没有独立预言 |
| 鲁棒性与安全性 | 5 | 4 | 不执行技能、不打开证据路径、非法输入非零退出。缺边仍可能被读成“没有流” |
| 可复现性 | 5 | 4 | 本环境 67 项通过、Ruff 通过、重复建图相等。3.10.9 与 SVG 未复核 |
| 阶段隔离与接口设计 | 5 | 5 | 未改 P03 提取器，没有差分、handoff、策略或风险标签 |
| 总分 | 100 | 88 | 无 Critical，无阻塞性 Major。测试通过没有用来补满算法分 |

## 15. 必须修复的问题

无。P04-1 至 P04-5 都不改变已证实的边方向、确定性或阶段边界，不阻塞 P05 的设计。

## 16. 可以延后处理的问题

- P04-1：接收者改用源码片段。可在后续整理证据指针时修。
- P04-2：补上指令方向断言。可在下一次修改 `test_graph.py` 时修。
- P04-3、P04-4：留给 P05 的读图契约。若 P05 需要可解释的缺席，再给未建模关系增加显式记录。
- P04-5：改验收记录中的提交说明即可。
- 本环境未复核的 3.10.9 与 SVG 字节数：保留为开发记录，不作为本审查已证实的结果。

## 17. 修复后的验收要求

若以后修改接收者标签或未知记录，至少重跑：

- `python -m pytest -q tests/unit/test_graph.py`
- `python -m pytest -q`
- 接收者反例 `foo . bar . baz()`，标签与源码片段一致，确定性仍为 `static`
- 传输句、`Accept`/`Return`、`f(g(), x=h())`、多行调用和 `make().process(x)` 的方向与未知记录保持本报告第 11 节的结果
- 全量测试仍包含并通过 P03 的 `test_scs.py` 与 `test_p03_review.py`

不要求为了这些 Minor 项重新打开 P04 实现。P05 设计本身必须写明第 16 节的读图约定。

## 18. 是否允许进入 P05

允许进入 P05 的设计。结论是 **PASS**。

P05 读取 p04.1 时采用这些已证实的语义：

- 指针是一次 SCS 数组中的位置，不是跨版本稳定身份
- `possible` 依赖指令重放或显式绑定；`static` 只表示输入中的语法结构
- `runtime_observation` 为 `none`
- 资源节点、前置声明和未绑定调用不能连成已证实的执行链
- transforms、sanitizes、跨语句数据流，以及星号或下标中的调用，没有在本图中评估
- Setext 首行仍可能作为 P03 主张进入图，边的确定性保持 `possible`
- 分析失败和 `failed` 状态不是良性标签，也不是恶意标签
