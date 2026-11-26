# P13 独立审查修复响应

**READY_FOR_REVIEW**。对象是同一 Skill 单个快照、固定观察键和调用上下文的有限坏前缀求值器。二审的主要问题是：已提交的数据前缀全部排除后，尚未建模的控制影响是否仍在违规上界内。

## 版本、工作树与边界

main，ed9238402f67d456983894cc79659ac8533f5b8a。修复前三份未跟踪文件与独立审查 §2 的 SHA-256 逐字节一致，依次为设计 c2d1f439b2cbdba3fdb1cd9693de74486dfa5298c6b10393ba138aab48deac1a、实现 c9ca92c03d6876e6cc666bc9bcf8b058a178af5c26a4fd721c12a9abe175a946、测试 a0d7aedf31824e352ceb985f5cd694413c9b5225aee2a3784921b4d01dd5764a。HEAD 不包含这三份文件。

修复前 git diff --numstat 显示 11 份已有跟踪差异：P07 preflight/report、P10 report、P12 design、P07 check_record/probe_modules/run_pair、两份 after.graphml、test_p10_baseline 和 third_party/sources.json。另有未跟踪的前置设计、验收记录、实现、测试和运行产物。此次写入范围为 docs/P13-design.md（先写修复设计）、src/dcfa/policy.py、tests/unit/test_policy.py，以及新增的本报告；零删除，未更改原审查或提交代码。

## 逐项核实、根因与验收

|问题|等级|核实结论|依据与根因|方案、影响及验收|处置|
|---|---|---|---|---|---|
|P13-N01|Minor|ACCEPTED|旧 upper 仅检查见证、候选和普通闭包证书。P04 缺少一般控制依赖边，空清单和已排除的值路径均可产生虚假的完整性排除。|把控制影响作为独立的上界来源；固定资源的保护性未知或为真时保留上界并输出原因。已证实非受保护的同一资源仍可在闭包内排除；同键矛盾分类抛错。|FIXED|
|P13-N02|Minor|ACCEPTED|三份内容哈希可核对，但 git status 为未跟踪。当前提交无法重建修复前或修复后的 P13。|维护者授权后归档并从干净树复测；既有文件的编写时间不能由事后提交独立证明。|DEFERRED|
|P13-S01|Suggestion|ACCEPTED|旧的不适用分支位于授权校验和边重放之前，无效边直接得到 not_applicable。|延后状态返回；不适用的良构输入仍保留独立状态，断裂或无效前缀报错。|FIXED|
|P13-S02|Suggestion|ACCEPTED|无精确授权时查表得到 None；当前契约没有授权全集证书。图覆盖也不能证明授权清单完整。|保留开放授权语义；若扩展封闭授权，需单独定义范围、来源和时效。本阶段仅固定现有语义。|DEFERRED|
|P13-S03|Suggestion|ACCEPTED|审查探针的若干边界未进入仓库。修复前新断言证实原有吸收、来源匹配和混合前缀行为。|新增独立合成回归，检查上下界、分类明细、图缺口与返回见证隔离。|FIXED|

无 Critical、Major。N01 的根源位于 P13 对 P04 表示边界的解释。P04 与 P05 的契约仍可使用，未发现需要解冻前置阶段的问题。P12 的对应关系没有单版本输入角色。

## 依据、算法与接口

P11 algorithm_spec §4 定义 L⊆W⊆U。完整性 Bad 包含不可信值影响与不可信控制影响两种可能。排除前者不能推出后者被排除。对固定上下文，protected 是可信环境对同一资源的分类。某条已提交前缀给出该资源的确定分类时可沿用至同键，矛盾的确定分类拒绝求值。分类随时刻或阶段变化的场景必须拆分上下文。即使存在数据见证，仍可同时报告控制通道未覆盖。保密规则仍依赖分析者对该键作出的完整覆盖声明，非空 graph_gaps 始终保留。

有限坏前缀来自 [Schneider](https://www.cs.cornell.edu/fbs/publications/EnfSecPols.pdf)。效果与阻断的背景见 [KnotScryer §III-D/E](https://arxiv.org/html/2610.32155v1)。[RogueOne](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF) 的跨版本域对差分未被调用。此次贡献是落实 P11 上界和契约校验的工程修正；未建立新的检测定理。

evaluate(graph,index,contract) 参数、四种状态及返回结构保留。原有调用方可能观察到完整性 safe 变为 unknown、新的原因 unrepresented_control_influence，或无效输入被拒绝。配置仍为确定性的保密、完整性两条规则，未引入模型、阈值或运行时观测。

## 修复前反例、独立算法和端到端回归

所有新增用例均先写预期，在旧实现上实际运行，且沿用临时合成目录 → P03 extract → P04 build_graph → P05 build_index → P13 evaluate，无核心 Mock。

|问题/测试|独立预期|旧结果|修复后与变体|
|---|---|---|---|
|N01 test_control_channel_open|缺控制通道时保留上界|两例误报 safe|空清单、非空但不可信来源为假均 unknown，核对原因与双界|
|N01 test_conflicting_resource_classification|同一键的资源分类冲突须拒绝|未抛错|拒绝；原资源不受保护例仍排除|
|S01 test_invalid_inapplicable|不适用也须拒绝非法边|未抛错|ValueError；原合法不适用例通过|
|S02/S03 test_review_absorption_and_gaps|无授权记录给未知，非私有为假仍足以排除|通过|保留排除项、未知授权和图缺口|
|S03 test_mixed_evidence_isolation|见证与候选共存；修改返回值不污染输入；授权来源换成效果节点失配|通过|三项均通过|
|S03 test_completion_oracle|枚举 private 与 bound 的九组三值输入，对每组独立穷举所有一致的布尔补全；全体为真/至少一个为真分别给出单前缀的下/上界|通过|九组一致；仅检验闭包内该有限保密片段|

## 命令及前后比较

Windows，项目 .venv/Scripts 下的 python 与 ruff。Python 3.14.0a5、dcfa 0.1.0、pytest 9.2.0、ruff 0.17.6、jsonschema 4.26.0、PyYAML 6.0.4。

|命令/时点|退出|通过|失败|跳过|
|---|---:|---:|---:|---:|
|python -m pytest -q（修改前）|0|174|0|0|
|python -m pytest -q tests/unit/test_policy.py（新增测试，旧求值器）|1|16|4|0|
|同命令，修复后|0|20|0|0|
|python -m pytest -q --ignore=tests/unit/test_policy.py|0|161|0|0|
|python -m pytest -q（最终工作树）|0|181|0|0|

ruff check .、git diff --check 均通过。Git 对既有文件提示换行符转换；该命令不覆盖未跟踪文件。独立审查的原临时探针未随报告交付，原脚本 NOT_RUN，其相关性质以仓库用例重建。类型检查、性能基准 NOT_RUN。前后全套耗时 6.47/5.85 秒，不能据此判断性能变化。

|对比项目|修复前|修复后|
|---|---|---|
|Critical / Major / Minor 待处理|0 / 0 / 2|0 / 0 / 1，归档延后|
|核心算法、风险结论和未知|普通闭包可排除完整性控制影响|未覆盖控制影响留在上界|
|独立参考算法一致性|九组三值补全一致|同一有限域一致|
|前置集成、原始证据|重放 P04/P05|同一接口，验证输出隔离，保留图缺口|
|异常、接口兼容|不适用掩盖坏前缀|合法输入形式兼容，畸形输入抛错|
|跨版本一致性、差分、修改归因、运行时配对、环境隔离与验证状态|不适用|不适用；专项动态、LLM、缓存、P12→P13 串联测试 NOT_RUN|
|性能|未建立基准|未建立基准|

## 剩余事项、冻结准备与二审重点

本阶段不是算法冻结节点。外部评价集保持隔离。可信环境仍须为语义谓词、绑定、可行性及覆盖提供独立来源；求值器未自动生成这些证明。二审应独立变换来源、用途、资源保护性和普通覆盖证书，核对没有控制边时上界的保守性，并验证有效见证仍能进入下界。维护者需另行决定归档时机；封闭授权表扩展亦留待后续正式设计。保留以下工作树指纹供独立复测。

- P13-design.md D00F248C9235D6C09AA84F05117C7914BF6E0D6BE5038E2E8685C510758DF44B
- policy.py 6F12897952E917BF4B4A60511CA2A362DABCEA27FA9BFCF61079760BD18D6024
- test_policy.py 83AD884A4BC9857327DF6062C08DC4245F28EEC7A511586DD69AE7822F2F3EB1
- algorithm_spec.md B9C06324775EF3AB2A32FE56C4ECAAED838301D243D63B0DA81D1ADFE75DAC92
