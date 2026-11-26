# P14 独立审查修复响应

**READY_FOR_REVIEW**。二审对象是固定策略键、固定有限上下文域上的静态状态差分。最重要的修正是先检查该键的动作是否适用于策略，再为缺失的报告引入未知布尔值。

## 版本、范围和可复现性

main，HEAD ed9238402f67d456983894cc79659ac8533f5b8a。修复前 Get-FileHash 核对了独立审查 §2 的全部五个 SHA-256（设计、示例、实现、测试、P11 规范），逐一相同。四项 P14 文件均未跟踪。修复前 git diff --numstat 中已有 11 个被跟踪路径的差异：P07 preflight/report、P10 report、P12 design、P07 check_record/probe_modules/run_pair、两份 after.graphml、test_p10_baseline、third_party/sources.json。另有未跟踪的前置文档、实现、测试、审查及复现产物。工作树基线见原审查 §2，并非干净提交。

本次修改 docs/P14-design.md、src/dcfa/policy_diff.py、tests/unit/test_policy_diff.py，新增本报告。先写设计与回归预期，再修改求值器。无删除、提交、推送、前置实现修改或验证配置变更。

## 逐项核实、计划与实际处置

|问题|等级|核实结论|核实依据与根因|处置及验收标准|状态|
|---|---|---|---|---|---|
|N01|Minor|ACCEPTED|修复前四个 P14 文件均为 ??，HEAD 无法独立重建本阶段。|报告记录摘要；待维护者授权归档后，从干净检出复跑。对集合算子无影响。|DEFERRED|
|S01|Suggestion|ACCEPTED|P11 规范末句反映 P12 时点。P13 evaluate 和 P14 compare 已实现有限片段，归因仍未实现。|在 P14 设计补记准确状态。冻结规范原句的原位更新留待获准维护前置文档。|PARTIALLY_FIXED|
|S02|Suggestion|ACCEPTED|certainty 比较允许布尔值集的基数；风险方向由区域决定，原设计没有解释该字段。|设计明确 unchanged/increased/decreased，保留字段及接口；用两种变化方向核对。|FIXED|
|S03|Suggestion|ACCEPTED|此前只依赖报告状态触发不适用分支，双侧缺报告时忽略键已确定的规则动作。|复用 P13 RULES 的动作条件，在可比且可靠对应的键上先处理不适用，再作布尔补全。双侧缺测不适用键排除于集合之外，适用键继续开放；单侧缺失不适用记录沿用不可比。|FIXED|
|S04|Suggestion|ACCEPTED|旧实现只接受小写字符且直接比较文本，等值摘要可被误作独立快照。|双方分别检查长度和 ASCII 十六进制字符，再忽略大小写比较。保留同对象自比较以及图、成员、报告、配置一致条件。|FIXED|

无 Critical 或 Major。S03 影响可能引入等区域的可信性，S04 影响未知证据自比较的精度。两项均为 P14 消费前置结果时的职责，前置阶段无需重新验收。

## 算法依据与研究边界

P11 algorithm_spec §4–5 的上下界限定于策略适用域。缺测给出 [0,1] 是对适用域内真实违规值的描述。静态已排除的策略动作没有这个布尔观察。摘要大小写仅涉及同一字节串的表示；P14 仍信任调用方提供的快照摘要。新增与缓解的界、六种整键标签及独立解释合并公式均沿用 P11。Schneider 的 [安全策略监视器](https://www.cs.cornell.edu/fbs/publications/EnfSecPols.pdf) 是单侧前缀的背景；[KnotScryer §III](https://arxiv.org/html/2610.32155v1) 与 [RogueOne](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF) 分别涉及能力流和域对差分。本次修正是数据表示及适用域处理，没有新增论文算法贡献。

## 反例、变体与参考算法

|问题及测试|理论预期|修复前|修复后及变体|
|---|---|---|---|
|S03 empty_reports_applicability|双缺测且保密策略作用于 write 时不适用；send 保留未知|write 错误进入 compared，send 正确|两例通过，不适用时无引入标签|
|S03 missing_and_reported_inapplicability|两份真实不适用报告排除；一侧少报仍不可比|本新增测试 NOT_RUN|两种输入通过|
|S04 digest_representation|同摘要不同写法应关联未知，两份报告不一致仍独立|大写、混合大小写失败；不同摘要、全角字符及错误长度负例通过|五组通过，核对新增上界和证书|
|S02 certainty_not_direction|安全→违规的信息量保持，违规→未知的信息量下降|通过|通过，同时核对确定新增|
|context_table_against_sets|两个上下文各取安全、违规、未知、缺测；独立枚举旧新真实集合并按严格包含比较可能标签|256 组一致|256 组一致，经过 compare，不调用 label 生成预期|

首次运行新套件时夹具将问号用作 Windows 目录名，得到 4 失败、17 通过；其中一个是测试输入准备失败。仅改为合法编号目录后重新验证旧实现，剩余三个才是已复现的产品反例。既有测试及预期均保留。

## 回归记录

Windows，项目 .venv/Scripts。Python 3.14.0a5、dcfa 0.1.0、pytest 9.2.0、Ruff 0.17.6、jsonschema 4.26.0、PyYAML 6.0.4。原始合成目录依次参与 P03 提取、P04 建图、P05 建索引，P12 对应和 P13 状态均真实生成，再调用 P14。没有执行样本。

|命令/时点|退出|通过|失败|跳过|
|---|---:|---:|---:|---:|
|python -m pytest -q，原工作树|0|193|0|0|
|python -m pytest -q tests/unit/test_policy_diff.py，旧实现、修正测试路径后|1|18|3|0|
|同命令，最终|0|22|0|0|
|python -m pytest -q --ignore=tests/unit/test_policy_diff.py|0|181|0|0|
|python -m pytest -q，最终|0|203|0|0|

ruff check . 与 git diff --check 退出 0。Git 提示已有文件未来索引写入时会转换换行符；diff 检查未涵盖未跟踪文件。原审查临时探针脚本 NOT_RUN，本次以仓库测试重建关键反例。类型检查与性能基准 NOT_RUN。全套基线 8.91 秒，最终 5.10 秒，未控制计时环境。

## 修复前后对比与冻结准备

|对比项目|修复前|修复后|
|---|---|---|
|Critical / Major / Minor 未结|0 / 0 / 1|0 / 0 / 1，归档待授权|
|核心算法及不确定性|缺测可为不适用键引入解释|先检查适用域；适用键保持双界|
|前置集成及证据|采用 P12、P13 和两侧原始见证|接口兼容，继续保留版本独立报告和图摘要|
|版本身份|只识别小写文本证书|两侧合法 ASCII 十六进制可不同大小写，其他一致性条件保留|
|验证目标、配对运行、沙箱、资源与超时、运行验证状态、动静证据融合、修改归因|不适用|不适用，专项动态测试 NOT_RUN，沙箱隔离 UNVERIFIED|
|测试计数、耗时|见上表|见上表，性能改善未经验证|

compare(before,after,mapping,contexts) 接口及 P11 §5 定义保持。配置来自双方可信标识，策略取 P13 RULES，无模型、Prompt、随机参数、超时器或动态验证预算。已验证的范围是合成输入的有限表。调用方仍需证明上下文完整、配置可比、报告对应真实快照。外部评价集保持隔离。本报告仅准备工作树版本证据。

## 待人工确认及二审重点

维护者决定归档时间和 P11 历史状态注记更新方式。二审重点复测不适用键双缺测、单缺测、不同文本表示的等值摘要，以及报告不同时对恒等关联的拒绝。建议从同一工作树独立枚举真实集合核对标签，不将 maintained 解读为安全。阶段停在 P14。

修复后 SHA-256：

- P14-design.md A2E1A3CD2B0DCAC26413C6CA7D1EA5056664902A05B5FF4ECA689D029B24C16F
- P14-example.json D1327C4E8ED0F54A7C81FC839C24D5A9544C26C0160344D8BF75EC550F86F16B
- policy_diff.py B880F88E353BE2E0C0DF3AC5F893DF37542DFA2FE4F275DCA6AE60D873CF46D4
- test_policy_diff.py 7C7E75214EA723D7073ED6688CEF3CAB6A14353042A8CD771D48C75F32A467BA
- algorithm_spec.md B9C06324775EF3AB2A32FE56C4ECAAED838301D243D63B0DA81D1ADFE75DAC92
