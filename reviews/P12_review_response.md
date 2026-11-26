# P12 独立审查响应

**READY_FOR_REVIEW**。本次验收对象是工作树中的单 Skill 跨版本能力对齐器。以下结果供第二轮审查复测。

## 版本、范围与复现条件

分支 main，HEAD 为 ed9238402f67d456983894cc79659ac8533f5b8a，与审查报告一致。该提交固定设计，未包含实现。修复前 alignment.py、test_alignment.py、P12-report.md 和 P11 三份规范尚未跟踪，故提交号无法证明工作树与审查快照逐字节相同。逐项重验当前工作树。原有已跟踪差异涉及 P07 两份文档、复现脚本及两份 GraphML、P10 报告与测试、third_party/sources.json。另有未跟踪的审查记录、复现输入、测试、日志等。未提交或推送。

本次写入范围为 docs/P12-design.md（先记方案）、docs/algorithm_spec.md（阶段状态注记）、src/dcfa/alignment.py、tests/unit/test_alignment.py，以及新增的本报告。无删除文件。Windows，项目 .venv，Python 3.14.0a5，pytest 9.2.0，Ruff 0.17.6，jsonschema 4.26.0，PyYAML 6.0.4。对齐采用有限观察契约，无模型、数值阈值或缓存。

## 逐项核实及处置

|编号|等级|判断|证据与根因|修复方案及验收|状态|
|---|---|---|---|---|---|
|N01|Minor|ACCEPTED|HEAD 中有设计，工作树中的实现、测试、完成报告未跟踪。提交不足以复现实验。|待负责人授权归档后从干净检出运行全部对齐测试。当前保留下方文件指纹。|DEFERRED|
|N02|Minor|ACCEPTED|align 输出的 role、slot_evidence 与 P05 witness 仍引用调用方对象。写旧侧可污染输入及新侧。|在输出边界分别深复制两侧证据。即使同一输入用于两侧，也必须独立，重复调用可重放。|FIXED|
|S01|Suggestion|ACCEPTED|规范末句仍称 P12 等待开始，与实际实现不符。|仅更新阶段状态，区分第 3 节有限子集及第 4、5 节。|FIXED|
|S02|Suggestion|PARTIALLY_ACCEPTED|原槽约束验证边，却完全信任局部声明中的语义名。边对端的版本内编号本身无法证明跨版本身份。|可选的双侧 neighbor_bindings 将实际端点映到人工契约角色，并核查 P05 见证；不一致抛 ValueError。原接口仍接受可信声明。|PARTIALLY_FIXED|
|S03|Suggestion|ACCEPTED|三个条件在原实现成立，原仓库测试未分别锁定。|持久化负例，检验弃判及两种观察投影。|FIXED|

## 理论与接口

依据 docs/algorithm_spec.md 第 3 节及 docs/P12-design.md。KnotScryer 的能力表示和 RogueOne 的程序流基线提供研究背景。本次端点一致性检查、有限角色对应与证据所有权属于项目实现。P04 提供边的方向、关系与版本内端点，P05 提供来源见证。独立编号可随版本变化。align(before, after) 中的 graph、index、contract 沿用原契约。新字段是版本内节点编号到语义名的字典；要使用登记表，两侧均须提供。返回证据保留登记表。P05 见证支持定位端点，登记表赋予的语义仍由契约提供。双方契约同时错误时，静态一致性检查无法发现该错误。输出信心仍为 conditional_on_contract。前置接口和持久性假设未变动。

## 最小反例、变体及独立对照

|问题/测试|预先推导的预期|改前|改后与变体|
|---|---|---|---|
|N02 test_evidence_isolation|旧侧修改不传播|断言失败，index 与 contract 均被污染|通过。同一输入复用、角色修改、清空槽列表与见证、反向修改输入、重复调用|
|S02 test_endpoint_contract|固定端点登记后改槽语义名应拒绝|未抛异常|通过。正确登记接受；声明冲突、单侧启用均拒绝|
|S03 test_single_candidate_requires_persistence|缺持续性声明的一对一仍未决|通过|通过|
|S03 test_unbound_competitor|一个未绑定候选足以破坏唯一性|通过|通过，三个实体均未决|
|S03 test_input_change_only|完整关系改变，安全投影相等|通过|通过，与原输出列、安全列变体互补|
|test_two_unit_reference|在可双射的两实体、两种完整角色的小域中，只有所有合法排列共有的对应才固定|NOT_RUN|通过，独立枚举排列并与实际配对集合比较。范围不含一般图上的任意匹配|

P12 用例从临时目录内合成 SKILL.md 和程序文本开始，经 extract、build_graph、build_index、人工有限契约进入 align。覆盖文件移动、改写、拆分合并、槽区分、证据隔离及未决对应。此端到端测试依赖人工提供的语义契约。

## 实际命令与修复前后对比

以下 python 和 ruff 均来自 .venv/Scripts。测试仅使用开发输入。

|实际命令与时点|退出|通过|失败|跳过|
|---|---:|---:|---:|---:|
|python -m pytest -q，原工作树|0|155|0|0|
|python -m pytest -q tests/unit/test_alignment.py，加入前五个反例，修实现之前|1|11|2|0|
|同上，修复后含独立对照|0|14|0|0|
|python -m pytest -q --ignore=tests/unit/test_alignment.py，修复后|0|147|0|0|
|python -m pytest -q，修复后|0|161|0|0|

ruff check . 与 git diff --check 均退出 0。Git 提示部分已跟踪文件下次写入索引时会转换换行符。diff 检查未涵盖未跟踪文件。类型检查与性能基准均为 NOT_RUN。完整套件最后一次耗时 4.38 秒，不能推断性能改善。证据复制的额外空间随输出证据大小增长。

|对比项目|之前|之后|
|---|---|---|
|Critical / Major / Minor|0 / 0 / 2|0 / 0 / 1 项延后归档|
|核心对应、弃判与两侧映射|依赖可信契约|保留原接口，登记模式核对端点；小域独立参考一致|
|证据真实性与完整性|结果可反向改写输入见证|两侧分别快照，仍信任上游索引与契约来源|
|风险差分、编辑真实性、直接/间接/共同/删除归因、无关修改隔离、配对执行|不适用|不适用，专项测试 NOT_RUN|
|前置模块兼容|原套件通过|147 项非对齐测试通过；合成端到端用例通过|

## 剩余事项与二审重点

负责人决定何时归档 N01，以及正式实验是否强制采用双侧登记表。二审应重放证据隔离、端点声明冲突和歧义弃判，区分可定位的端点、人工角色和独立证实的跨版本身份。核查登记表模式的错误输入及旧契约兼容性。此次工作没有提供风险归因或自动释义的新证据。阶段停在 P12，等待独立审查。

## 修复后文件 SHA-256
- P12-design.md 0052B83BE9B698C87DE8DFE43E3B3DAEAE00B50B577604860A1468C80B299B33
- algorithm_spec.md B9C06324775EF3AB2A32FE56C4ECAAED838301D243D63B0DA81D1ADFE75DAC92
- alignment.py 4B6F20EF23D5541949A1A04EE389B1B6E379BF0D05B3C4C91EC0A5D61BC36100
- test_alignment.py 37ABEDC2A9C65CB9664827E2D5E9D5AD78B768280C411CF61D6C8080647F2CFA
