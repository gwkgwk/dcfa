# P16 独立审查

结论：**PASS**（87 / 100）。可以申请进入 P17，仍须项目负责人确认。本次没有修改实现，没有读取 `evaluation.ndjson`，也没有启动 P17。

P16 是同一 Skill 两份只读快照上的集成入口 `analyze_update`。它按顺序调用已验收的提取、建图、索引、对齐、策略求值、有限上下文差分和位置关联。`completed` 只表示指定查询已经跑完。`maintained` 表示契约下的违规集合相同。`causal_status` 仍是 `not_established`。当前结果不能当作检测性能、归因准确率或已冻结算法。

## 1. P16 正式任务定义

仓库里没有 P00—P20 总任务书，也没有单独的 P16 任务书或完成报告。`docs/P00-design.md` 只规定后续阶段另行提交设计。相对“正式任务书”的需求验收为 **UNVERIFIABLE**。本次把已存在的 `docs/P16-design.md` 当作阶段合同，并与 `docs/algorithm_spec.md`、`docs/research_problem.md` 对照。

合同对象是固定环境中同一 Skill 的两份只读快照。调用 `analyze_update(old_path, new_path, config)`。`config` 由可信调用方提供，与待测目录分开。`configuration` 是共同工具、精度和预算的版本标识。`before` / `after` 各带一份 P12 契约，可选 P04 `bindings` 与可信 `binding_file`。`queries` 预先给出 `id`、`key`、`contexts`，以及两侧 `members` 和 P13 契约序列。分析者负责把契约绑到图摘要；缺报告保持缺测。空查询只产生表示与对齐，并标记未评价。一次调用返回全部查询，各自保留差分与关联。

失败语义：文件读取、解析或快照一致性失败时保留侧别和失败证据并停止比较。可信契约非法时异常退出，不产生安全结论。总状态成功只表示完成指定查询。

设计写明的验收例：

- 相同快照上的未知自比较保持，且没有新增上界。
- 在可信角色绑定下，改名和同义指令的策略结果保持。
- 一个上下文持续违规、另一个新增时为加剧；交换两侧为缓解。
- 未知到违规不能确认成引入。
- 已绑定常量变化的证据回到两版真实行。
- 纯指令与纯程序走同一入口；混合快照按真实图边分别重放；没有桥接证据时不产生跨模态路径。

P15 终审对下游的约束也纳入本次检查：位置证据使用 `matched_lines`；常量依赖和 `not_established` 不能写成已证实原因。仓库没有 P17 文件，下游依赖为 **UNVERIFIABLE**。

规范第 5 节的最小充分编辑集不在本阶段合同内。实现保留 `causal_status=not_established` 与 `joint_sufficiency=unknown`，没有把该能力写成已经完成。

## 2. 审查范围及代码版本

| 项 | 值 |
|---|---|
| 分支 | `main` |
| HEAD | `ed9238402f67d456983894cc79659ac8533f5b8a` |
| 该提交的含义 | 只预注册了 P12 对齐合同，不包含 P13—P16 实现 |
| 解释器 | Python 3.14.0a5（项目 `.venv`） |
| 基线标签 | `rogueone-style-baseline-v1.0.0` 剥开后为 `cde3341d914a62997be57770d5b8c8797dc8816d` |
| 冻结候选 | `docs/P16-freeze-candidate.json` 状态为 `pending_independent_review`，`external_evaluation=not_run` |

本阶段未跟踪文件：`src/dcfa/update.py`、`tests/unit/test_update.py`、`docs/P16-design.md`、`docs/P16-example-config.json`、`docs/P16-analysis.json`、`docs/P16-freeze-candidate.json`。P12—P15 的实现和设计也仍未进入该提交。

对 `program_flow.py`、`trust_diff.py`、`graph.py`、`evidence.py`、`scs.py` 执行 `git diff --numstat` 无输出。`policy.py`、`policy_diff.py`、`alignment.py`、`attribution.py` 相对 P15 终审记录的摘要未在本阶段被修改；冻结候选中的 18 个路径经独立重算全部一致，其中包括：

- `src/dcfa/update.py` = `84f24d8cb2e36af91aec319e40fa3907bbc8cd6fb18bb08639d0a0f2b6e25ae2`
- `src/dcfa/policy.py` = `6f12897952e917bf4b4a60511ca2a362dabcea27fa9bfcf61079760bd18d6024`
- `src/dcfa/attribution.py` = `38f510f81e3b7435ed706d374da1cf8eed145d819ef4f64df58345f1dbb338f2`

工作区里存在未跟踪的 `evaluation.ndjson`。`src` 没有引用该路径。本次没有打开它。

审查阅读了 P16 设计、示例配置、样例输出、冻结候选、`update.py`、`test_update.py`，以及 `align`、`evaluate`、`compare`、`attribute`、`scan`、`build_graph`、`build_index` 的实际参数。没有把开发说明当作证据。

## 3. 执行摘要

集成顺序与设计一致：每侧扫描字节并提取 SCS、建图、建索引、核对清单摘要；两侧都成功后做一次对齐；每个预声明查询分别求值、差分、关联。查询之间没有汇总分，也没有互相抵消。

独立预期来自规范第 5 节的整键条件，不来自 `label()`。一个上下文的违规集合保持为 `{a}`、新版成为 `{a,b}` 时，实现给出 `aggravated`；交换后为 `mitigated`。旧集合为空且新集合非空时为 `introduced`。旧侧缺报告时整体为 `unknown`，区域前状态为 `missing`。相同字节且报告相同的未知自比较为 `maintained`，`identity_certificate` 为真，新增上界为假，关联为空。违规集合不变而字面量改变时，文件编辑仍在，关联为空。两个键一个引入、一个消除时，两条记录同时留下。

混合快照中，程序见证的 `matched_lines` 只落在 `main.py`，指令见证只落在 `SKILL.md`，图中没有把 `instruction_action` 与 `call_expression` 直接连起来的边。纯授权变化没有文件编辑，关联的确定性为 `definite`，因果状态仍是 `not_established`。插入首行空行后，调用所在区间从第 1 行变为第 2 行。`docs/P16-analysis.json` 与用示例配置重新执行的结果一致，配置摘要为 `e3e9b80754b90aa3c31f23521ef27530e538305a98fa2f5d844b46abcfcf10ad`。

没有发现未解决的 Critical 或阻塞性 Major。

## 4. 需求完成度矩阵

| 需求 | 对应实现 | 对应测试 | 实际证据 | 完成状态 |
|---|---|---|---|---|
| 正式任务书 | 无 | 无 | 仓库无独立任务书 | UNVERIFIABLE |
| 两份快照、可信配置、一次返回全部查询 | `analyze_update` | `test_modalities_and_direction` | 两通道同时为 `aggravated` | COMPLETE |
| 读取、解析、清单不一致时停止比较并保留侧别 | `_snapshot` | `test_parse_failure` | 坏语法与缺 `SKILL.md` 均为 `analysis_failed`，结果为空 | COMPLETE |
| 有序路径字节摘要，并调用 P12 | `snapshot_digest`、`align` | `test_snapshot_digest`、`test_no_queries_or_unresolved_identity` | 空查询状态为 `no_queries`，输出仍含 `alignment` | COMPLETE |
| 每查询调用 P13、P14、P15 | 第 87—99 行 | 模态、方向、引入、未知测试 | 区域下界与规范例子一致 | COMPLETE |
| 多查询互不抵消 | 逐条 `results.append` | 仓库测试未覆盖反向组合 | 探针同时得到 `introduced` 与 `resolved` | COMPLETE |
| 缺报告保持缺测 | 把调用方契约原样交给 `evaluate` | `test_new_versus_existing` | 空契约时 `before=missing`，整体 `unknown` | COMPLETE |
| 非法可信契约异常退出 | 未捕获 `ValueError` / `KeyError` | 仓库测试未覆盖 | 空配置、重复 id、不同 Skill、坏图摘要、错误 members 均抛出 | COMPLETE |
| 未知自比较保持且无新增上界 | 传入两侧快照摘要，由 P14 发恒等证书 | `test_identity_unknown_and_equivalence` | `identity_certificate` 为真，新增上界为假 | COMPLETE |
| 可信绑定下改名的策略结果保持 | 契约锚点进入 P12，策略集合进入 P14 | `test_equivalent_update` | 策略 `maintained`；对齐投影 `full.state=unknown` | COMPLETE |
| 持续加新增为加剧，对换为缓解 | 原样保留 P14 `overall` | `test_modalities_and_direction` | 上下文 `a` 的持续下界为真，`b` 的新增下界为真 | COMPLETE |
| 已绑定常量回到真实行 | 保留 P15 `matched_lines` | 仓库测试检查第 1 行 | 首行插入空行后区间为 `[2,2]`，且只在 `main.py` | COMPLETE |
| 三模态同一入口，缺桥接不跨模态 | 不自行构造 bindings | 三种 `mode` | 无指令节点到调用节点的直连边；证据文件不交叉 | COMPLETE |
| 最小充分编辑集 | 未实现 | 因果字段断言 | 始终 `not_established` / `unknown` | 不在合同内，未伪称完成 |
| 阶段完成报告 | 无 | 无 | 无 `docs/P16-report.md` | MISSING |
| 算法冻结 | 候选清单 | 18 个摘要复算一致 | 状态仍是 pending，且没有对应提交 | PARTIAL |
| P17 输入要求 | 无 | 无 | 无 P17 文件 | UNVERIFIABLE |

未发现只声明接口而返回硬编码标签的路径。样例 JSON 能由当前代码重新生成。设计没有把外部评价写成已经完成；候选文件写明 `not_run`。

## 5. 算法正确性审查

`analyze_update` 的数据契约与前置函数一致。

- `_snapshot` 用 `scan` 收集字节，再用 `extract`、`build_graph(summary, bindings)`、`build_index(graph, root, binding_file)`。清单摘要比较的是扫描字节与索引里 `skill/` 文件的 SHA-256。
- 任一侧失败则返回 `analysis_failed`，不调用 `align`。成功路径才执行 `align(old, new)`。
- 每个查询用该侧图和索引调用 `evaluate`，再把报告、members、快照摘要和同一次对齐交给 `compare`，最后把两侧字节、对齐和差分交给 `attribute`。
- 成功结果经过 `deepcopy`。实现没有调用 `trust_diff` 或 `program_flow`，没有把冻结基线当成 DCFA 结论。

标签检查使用的是集合条件，不是被测函数的标签表。`[False, True]` 到 `[False, False]` 表示旧违规集合 `{a}`、新集合 `{a,b}`，整体为范围扩大；代码中的英文 `aggravated` 与 P14 已验收的对应关系一致。反向为 `mitigated`。`[True, True]` 到 `[False, True]` 为 `introduced`。旧侧无报告时不能确认引入。相同未知报告的自比较不产生新增上界。

改名例 `send(x)` 与 `publish(y)`、指令大小写变化，在调用方给出相同锚点和相同授权时策略结果为 `maintained`。对齐记录里的观察投影仍是 `unknown`。因此该结果表示契约下的违规集合相同，同时保留“观察等价尚未证明”。实现没有自行把 `publish` 判定为 `send` 的同义词。

位置关联沿用 P15。操作数见证的六处 `matched_lines` 都是 `main.py` 的第 1 行；指令见证都在 `SKILL.md`。首行插入空行后，操作数区间变为第 2 行。纯授权变化的 `files` 为空，关联存在，语义依赖为空，因果状态不变。违规集合不变而参数从 `1` 改为 `2` 时，编辑保留，关联为空，既有风险没有被记成新增。

额外的 `README.txt` 在契约按新图重建后仍得到 `aggravated`，且不出现在查询结果中。过期的边序号或错误 members 会抛出 `ValueError`，不会返回一条安全结论。不同 Skill、空白 `configuration`、重复查询 id、错误图摘要同样抛出。

`src` 中没有 `subprocess`、`exec` 或 `eval`。探针输入都是临时目录中的合成文本。

已知边界，本次复测仍然成立：

- 策略事实和授权来自外部契约。
- 一条常量参数规则只说明两版字面量不同，不证明该编辑造成了违规。
- 相同字节的恒等证书不能推广到仅仅改名的快照。
- 规范第 5 节的最小充分编辑集没有实现。

## 6. 科研严谨性审查

P16 没有新的阈值、权重或按样本名称分支的规则。`configuration` 只作为版本字符串传入差分，并进入配置摘要。算法选择没有使用外部评价标签。

样例输出是合成夹具的真实执行：示例配置与 `scenario` 生成的配置规范化后相同，`P16-analysis.json` 与重新调用 `analyze_update` 的规范化结果相同。这是集成冒烟记录，不是外部实验，也不是性能结论。

冻结候选与当前文件字节一致，但状态明确写着等待独立审查，外部评价未运行。工作树没有提交，因此它还不是可检出的冻结点。规范第 56 行仍写着第 4、5 节尚未实现，与 P13—P16 的工作区事实不一致。见 P16-N01。

对比基线、消融、数据划分、统计检验和指标实验不是本阶段职责。已核对冻结基线所在的跟踪文件没有差异，标签 `rogueone-style-baseline-v1.0.0` 仍指向 `cde3341`。没有发现为了让集成结果好看而改写 P08—P15 的行为。

## 7. 工程质量审查

`update.py` 约 100 行，只做编排和快照一致性门。查询 id 要求非空字符串且不重复。图摘要不一致、成员不属于对齐单元、上下文非法时，错误从既有模块向外传播。

成功报告与内部对象隔离。失败报告是浅拷贝，见 P16-S02。调用之间没有缓存，所以这不会污染下一次分析。

安全方面：入口不执行待测脚本；扫描仍使用既有的大小、深度、重解析点和路径约束。命名流未检查时返回 `analysis_failed`，原因包含 `named_stream_unexamined`，不给出比较结论。这比“继续并保留缺口”更保守，与“清单未完整核验则停止比较”相符。符号链接创建在本机返回权限不足，本次未能复测该分支。`mypy` 未安装。

全量测试 223 项通过，说明本次新增入口没有破坏已有单元测试所覆盖的 P00—P15 行为。P17 接口尚未定义，因此不存在一份可以被破坏的下游合同。

## 8. 测试验证结果

仓库测试先写授权事实，再断言整体标签，没有用 `analyze_update` 的输出给自己当预期。覆盖了摘要顺序、三种模态、方向对换、未知与自比较、改名保持、解析失败、引入与缺报告、锚点缺失和空查询。断言包括 `matched_lines == [1, 1]`、`causal` 语义所依赖的关联字段，以及失败时结果为空。

独立探针的理论预期写在执行之前。第一份探针有 4 条断言写窄了：操作数路径有六处同行证据，纯授权变化会同时作用于指令通道，保持例也包含两个通道，插入空行后的命中数同样多于两处。核对原始值后，这些区间都落在预期文件的预期行上，标签也符合集合表。该偏差是探针预期过窄，不是实现错误。第二份探针确认了文件分离。第三份探针 11 项全部通过。

| 命令 | 退出码 | 结果 |
|---|---:|---|
| `python -m pytest -q tests/unit/test_update.py` | 0 | 9 passed |
| `python -m pytest -q` | 0 | 223 passed，0 failed，0 skipped，约 4.65s |
| `ruff check src/dcfa/update.py tests/unit/test_update.py` | 0 | passed |
| `ruff check .` | 0 | passed |
| 临时探针 `p16_probe3.py` | 0 | 11 passed |
| `python -m mypy` | 未运行 | 环境无 mypy |
| 符号链接复测 | 未运行 | `mklink` 返回权限不足 |
| 外部评价集 | 未运行 | 按审查边界禁止启动 |

全量 223 含工作区中尚未提交的前序测试。它证明当前工作树的单元测试通过，不能从提交 `ed92384` 单独复现。

## 9. 全部问题及严重程度

### P16-N01 规范状态句仍与工作区实现相反

- 严重程度：Minor
- 证据状态：CONFIRMED
- 位置：`docs/algorithm_spec.md` 第 56 行
- 对应定义：规范第 6 节的阶段状态；P16 设计把伪代码标为第 1—5 节
- 描述与原因：该句仍写 P12 只实现第 3 节，第 4、5 节尚未实现。P13—P15 已在工作区实现有限子集，P16 已经调用它们。该文件在 P16 之前就是未跟踪状态，本阶段没有改它。
- 影响：只读规范的人会认为差分和归因不存在。运行结果本身没有把未实现的最小充分编辑集写成已证实原因。
- 复现：阅读该行，再对照 `policy_diff.py`、`attribution.py`、`update.py` 的导入。
- 修复：用单独的状态说明区分第 4、5 节的有限已实现子集和仍未实现的最小充分编辑集。不要把该说明写成实验结论。
- 验收：状态句能同时看到求值、有限差分、位置关联和“最小充分编辑集未实现”。
- 是否阻塞：否。

### P16-N02 实现不在当前提交中

- 严重程度：Minor
- 证据状态：CONFIRMED
- 位置：工作区未跟踪的 `src/dcfa/update.py`、`tests/unit/test_update.py` 与四份 `docs/P16-*`
- 对应需求：阶段实现要能由版本标识复现
- 描述与原因：HEAD `ed92384` 不包含这些文件。冻结候选只记录了工作区字节，状态仍是 pending。
- 影响：不能把该提交当作 P16 的实现标识，也不能把候选清单当作已经冻结的算法。当前工作区中的行为已经复测。
- 复现：`git status --short` 显示上述文件为 `??`；`git cat-file -e HEAD:src/dcfa/update.py` 会失败。
- 修复：由负责人决定归档范围，只纳入本阶段文件，并在归档提交上重算摘要。
- 验收：干净检出该提交后，P16 测试与本次探针可复现，摘要与提交内容一致。
- 是否阻塞：不阻塞工作区合同验收。阻塞把 `ed92384` 或 pending 候选当成冻结版本。

### P16-S01 仓库测试没有锁定若干已通过的集成性质

- 严重程度：Suggestion
- 证据状态：CONFIRMED
- 位置：`tests/unit/test_update.py`
- 对应需求：设计中的跨模态隔离、查询互不抵消、纯授权变化和真实行区间
- 描述：现有 9 项测试覆盖了主路径。反向键、纯授权、插入空行、证据文件不交叉，以及五类非法契约，只在本次临时探针中验证。
- 影响：这些性质若回退，当前仓库测试不一定失败。本次执行没有发现相应的实现错误。
- 复现：临时探针 `p16_probe.py` 与 `p16_probe3.py`。探针不在仓库中。
- 修复：把上述预期加入 `tests/unit/test_update.py`。预期继续由授权集合和源文本决定。
- 验收：新增测试在当前实现上通过，并在故意交叉两条见证文件时失败。
- 是否阻塞：否。

### P16-S02 失败报告没有与成功报告同样隔离

- 严重程度：Suggestion
- 证据状态：CONFIRMED
- 位置：`src/dcfa/update.py` 第 73—74 行返回浅拷贝；第 100 行成功路径使用 `deepcopy`
- 对应需求：失败结果只作为证据，不参与下一次比较
- 描述：失败返回值与当次构建的快照对象共享结构。下一次调用会重新扫描，没有模块级缓存。
- 影响：调用方若修改失败报告中的图，只影响自己持有的对象。
- 复现：构造一侧语法错误，修改返回值中的另一侧图对象；再次调用结果仍由磁盘决定。
- 修复：失败返回同样 `deepcopy`。
- 验收：修改返回值不改变该对象的原始嵌套内容。
- 是否阻塞：否。

## 10. 修复优先级

1. 归档前先处理 P16-N02，并同时修正 P16-N01 的状态句。二者都不改变已复测的集合结果。
2. P16-S01 适合在归档时一并补上，用来防止跨文件证据和反向查询回退。
3. P16-S02 可以随后处理。

不需要为了进入下一阶段而扩大 P16 的算法范围。最小充分编辑集、动态验证、指标和外部评价仍不属于这次修复。

## 11. 量化评分

| 评价维度 | 满分 | 得分 | 依据 |
|---|---:|---:|---|
| 原始任务完成度 | 15 | 13 | 设计中的入口、失败停止、空查询和验收例已复测。缺正式任务书与完成报告，规范状态句未更新 |
| 算法正确性 | 25 | 23 | 独立集合预期、行区间、跨文件证据和因果边界均符合当前合同。观察投影未知与策略保持同时存在，调用方必须读对齐记录才能区分 |
| 科研方法严谨性 | 20 | 18 | 合成样例可重算，候选冻结未冒充正式冻结，基线跟踪文件无差异。规范末句仍与实现相反 |
| 软件工程质量 | 10 | 9 | 编排边界清楚，非法契约向外抛出。失败报告是浅拷贝 |
| 测试覆盖与有效性 | 15 | 12 | 9 项仓库测试检查标签和失败，不是类型冒烟。反向键、纯授权、插入行和跨文件隔离尚未进入仓库测试 |
| 安全性与健壮性 | 5 | 4 | 不执行待测脚本，失败不返回安全结论。符号链接分支本次未能复测 |
| 可重复性 | 5 | 3 | 候选摘要和样例报告与工作区一致。实现不在 HEAD，pending 候选没有提交 |
| 阶段边界与接口兼容性 | 5 | 5 | 调用已验收函数，全量 223 项通过，没有改写基线或因果结论 |
| 总分 | 100 | 87 | 无未解决 Critical 或阻塞性 Major |

缺少正式任务书和 P17 合同的部分没有给满分。分数不把本阶段提升为检测性能证据。

## 12. 最终验收结论

**PASS。**

相对 `docs/P16-design.md`，集成入口、失败语义和列出的验收例已经实现，并经独立探针复核。没有未解决的 Critical 或阻塞性 Major。P16-N01 与 P16-N02 保留为非阻塞限制：归档和引用版本之前必须处理，它们不改变当前工作区里的比较结果。

以下能力没有被本次通过所证明：

- 编辑是违规变化的原因，或某个编辑集最小且充分。
- `maintained` 是安全证明，`introduced` 是恶意更新，`analysis_failed` 是良性。
- `completed` 表示检测成功。它只表示指定查询已经完成。
- 外部数据上的检测率、归因准确率或泛化能力。
- 算法已经冻结。候选文件仍是 `pending_independent_review`。

## 13. 是否建议进入 P17

可以申请进入 P17。只有项目负责人确认后才能进入。本次不创建 P17，也不启动外部评价。

仓库尚未定义 P17。下一阶段若消费本输出，需要单独写输入合同，并保持这些字段的既有含义：`matched_lines` 是见证与编辑块的交集，`candidate_edits` 仍指向整段编辑，`not_established` 不是已证实原因，`maintained` 不是安全，`introduced` 不是恶意意图，`completed` 不是检测成功。
