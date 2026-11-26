# P15 独立审查修复响应

**READY_FOR_REVIEW**。本轮核实的问题是风险见证的位置证据能否精确到对应版本的相交行。候选编辑块仍可重放，风险方向及因果证据等级继续取决于原有契约。

## 版本、工作树及修改范围

分支 main，HEAD ed9238402f67d456983894cc79659ac8533f5b8a。修复前 Get-FileHash 核对了原审查 §2 的五项 SHA-256，设计、示例、实现、测试及数学规范均逐字节一致。四份 P15 文件未跟踪，HEAD 不能作为实现版本。git status --short --branch 与 git diff --numstat 显示 11 个既有跟踪差异，涉及 P07 preflight/report、P10 report、P12 design、P07 check_record/probe_modules/run_pair、两份 after.graphml、test_p10_baseline 和 third_party/sources.json。另有未跟踪的前置文档、实现、审查、测试和复现产物。

本轮先写 docs/P15-design.md 中的修复设计，再添加 tests/unit/test_attribution.py 的测试，修改 src/dcfa/attribution.py 的 replay，重新生成 docs/P15-example.json，新增本报告。零删除。前置阶段和原审查保持原样。冻结的提取、图、证据、流分析、域对差分模块均在本次写入范围之外。

## 问题核实、根因与处置

|编号|等级|核实结论|依据与根因|方案与验收|状态|
|---|---|---|---|---|---|
|P15-M01|Minor|ACCEPTED|原 replay 检查行区间重叠，但仅输出 hunk 编号、原点和完整见证。相邻行合并后，消费者只能自己重新计算交集。最小反例中删除旧第 1 行同时修改旧第 2 行，整块覆盖两行。|在共用的证据映射处增加每个来源的 matched_lines，按版本与来源分别计算。旧第 2 行、新第 1 行才是该调用的命中区间；保留原件、整块、语义依赖和因果未知。|FIXED|
|P15-N01|Minor|ACCEPTED|git status 显示四个 P15 路径为 ??。独立审查快照可核对，干净检出不能复现实现。|由维护者授权归档，之后从干净检出核对指纹并复测。此次按要求未提交或推送。|DEFERRED|
|P15-S01|Suggestion|ACCEPTED|规范末尾保留 P12 时点的进度句；P13 evaluate、P14 compare、P15 attribute 及集成测试已展示后续有限实现。|P15 设计已分别记录单侧求值、差分、有限关联和未实现的最小充分集。冻结规范中的历史进度句留待维护者归档时更新。|PARTIALLY_FIXED|

两个 Minor 均为审查原定严重程度。没有 Critical、Major 或前置阻塞性缺陷。M01 影响下游消费的位置精度；原输出没有宣称整个 hunk 都是语义原因。若日后评估行级定位，应消费 matched_lines，不能用文件名或整个 hunk 代替。

## 正确行为、接口与理论依据

对侧 s、编辑块区间 H、经 P05 哈希和片段重放的见证区间 W，位置证据是两个闭区间的交。若交非空，输出 [max(H.start,W.start), min(H.end,W.end)]。交为空没有位置命中；插入和删除的空侧没有虚构行号。匹配精度限于行。candidate_edits 是索引；消费精确位置应读取 paths[].locations[].edits[].matched_lines，edit_targets 中同样提供该字段。旧字段保持兼容。没有修改 P14 的上下界、P13 授权或 P12 的身份定义。

依据为 docs/algorithm_spec.md §5 的 Rel(d,w) 与 P05 见证契约。位置重叠只提供位置证据，常量位置参数还须有 AST 和绑定关系。模型内最小充分集需要另外的反事实及子集验证。P15 属于项目扩展。[RogueOne](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF) 提供域级差分背景，[KnotScryer](https://arxiv.org/html/2610.32155v1) 提供能力流研究背景；二者均未用作行级归因真值。本次是工程证据精度修复，没有新增理论贡献。

## 独立预期、反例及回归结果

|问题与用例|独立预期|修复前|修复后及变体|
|---|---|---|---|
|M01 test_adjacent_hunk_intersection|按手写源程序核定调用行；旧行 2→新行 1、旧行 1→新行 2、两侧均为中间行 2。独立 ast.parse 提取该行参数值|3 项因无相交区间失败|3 项通过；相邻删除、相邻插入、上下两侧均有无关变化；常量依赖和因果未知均保持|
|M01 test_multiline_clips_both_ways|变更行 1–3，调用行 2–5，实际交集 2–3|缺 matched_lines，失败|通过；不会扩大到完整见证，也不会扩大到整块；没有新增语义依赖|
|M01 负例 test_authorization_only_has_no_edit|只改授权且源码相同，新增区域存在，编辑及语义依赖为空|通过|通过|
|原 6 项|隔行无关编辑、注释、无风险变化、篡改证据、增删、多个 hunk|通过|通过|

新测试先在原实现运行。预期行号直接由合成源码给出，常量转储由标准库独立计算；两者均未调用 replay 推导预期。重生成示例时，将新字段从新 JSON 递归移除后与旧示例作结构相等断言，实际通过。此检查包含原始见证、文件摘要、P14 状态及语义依赖。端到端管线经过临时合成 Skill → P03/P04/P05 → P12/P13 → P14 → P15；脚本内容仅供静态分析。

## 实际环境、命令和前后对比

Windows，项目 .venv/Scripts，Python 3.14.0a5、dcfa 0.1.0、pytest 9.2.0、Ruff 0.17.6、jsonschema 4.26.0、PyYAML 6.0.4。编辑块由 SequenceMatcher(autojunk=False) 计算。单一已绑定常量参数规则；无模型、Prompt、随机采样或评价配置。本阶段无正式实验协议或数据集版本输入。

|命令与时点|退出|通过|失败|跳过|
|---|---:|---:|---:|---:|
|python -m pytest -q，修复前|0|209|0|0|
|python -m pytest -q tests/unit/test_attribution.py，新增反例、旧实现|1|7|4|0|
|同命令，修复后|0|11|0|0|
|python -m pytest -q --ignore=tests/unit/test_attribution.py|0|203|0|0|
|python -m pytest -q，修复后|0|214|0|0|

ruff check . 与 git diff --check 退出 0。Git 给出现有文件换行符转换提示，diff 检查没有覆盖未跟踪文件。独立审查的临时探针原脚本 NOT_RUN；上表记录本轮重建的审查反例。类型检查、性能基准 NOT_RUN。全套耗时 9.40/5.13 秒未控制环境，不能推断性能改善。

|对比项目|修复前|修复后|
|---|---|---|
|Critical / Major / Minor 未结|0 / 0 / 2|0 / 0 / 1，归档延后|
|核心行为与接口|记录重叠 hunk 及来源|同一位置对象新增版本内相交行，保留原接口|
|前置集成、失败和不确定性|真实图、摘要、路径校验，P14 possible 传播|同一契约；摘要篡改仍失败；语义和因果等级未升级|
|数据划分、标签隔离评测、基线公平性、消融、预测及指标、统计计算|不适用|不适用，专项实验 NOT_RUN；未接触冻结评价数据或标签|
|实验真实性、冻结准备|工作树合成实验，缺已归档实现|示例重放一致并记录指纹，尚不具备正式实验冻结条件|
|测试通过/失败/跳过|209/0/0|214/0/0|

## 局限、人工事项与二审重点

证据只支持已验证行的相交区间。同行多个表达式、同一 hunk 的独立语义及一般因果路径没有因此得到证明。没有独立真实数据集证据级 Ground Truth，也没有归因准确率或基线性能声明。无需重新验收前置算法。维护者需决定版本归档及历史规范进度更新。二审重点是重放两侧不同偏移的 hunk、多行片段的双向裁剪、授权变化无编辑以及示例兼容性。当前停在 P15。

修复后 SHA-256：

- P15-design.md CBC7CD39105E980D914A2BBBA88E5BE8B29C8FAD903BFC2DF8183E8155578A4E
- P15-example.json 2C50B2F6D8C69F9807739FF3A591BD2CD039893C044477E31C356C9AF97DD3EB
- attribution.py 38F510F81E3B7435ED706D374DA1CF8EED145D819EF4F64DF58345F1DBB338F2
- test_attribution.py E5A8EDC03A4CC971624DFC553759C18D4A56E65571E9C9F7DA227F5D593E9520
- algorithm_spec.md B9C06324775EF3AB2A32FE56C4ECAAED838301D243D63B0DA81D1ADFE75DAC92
