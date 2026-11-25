# P09 程序级域差分运行报告

设计先行提交 28e07ea。实现 src/dcfa/trust_diff.py，独立测试 tests/unit/test_trust_diff.py。运行 python -m dcfa.trust_diff OLD.json NEW.json；程序接口 compare(before, after)。两份输入须来自同一 Skill、相同 P08 配置、相同逻辑入口。P08 JSON 没有 Skill 身份或配置签名；调用方负责选择版本及保证来源。入口路径不一致按不可比处理。工具只使用标准库，分析过程不导入 P08、SCS 或 DCFA 策略模块。

依据及根规则见 [运行前设计](P09-design.md)。规范键为有序域名二元组；域内自流排除。旧、新流分别在 before.flows 与 after.flows。每条保存共同对象及两条根到对象的路径，路径边编号为本侧 edges 数组的零基下标，节点 ID 查同侧 nodes；源码位置沿用 P08 的相对路径和行号。每对域仅保留一个存在性见证。CLI 另外记录实际读到的输入 JSON 字节 SHA256；这不能替代原始 Skill 源文件哈希。

added、deleted、retained 分别记录增加、删除、保持。alerts 引用新增流的版本和域对，按此键可回查 after.flows。模块涉及未核验导入时应连同该侧 import_assumptions 解读。所有结论限定于两个入口的 P08 可能流模型。未进入函数保留原覆盖信息。partial 仍可给出已观测的正见证；对侧缺乏完整观测时无法断定该流先前或后来不存在，单侧候选保留在 unresolved_before / unresolved_after。读取、JSON、图结构错误单独登记，CLI 以 1 表示存在未知或不可比结果，以 0 表示本子集比较完成。没有风险分值或恶意标签。

独立预期示例：旧版 first.emit('a')，新版 second.emit(first.read('a'))，导入声明分别为 first、second。局部值到 first 的关系保持，局部值到 second 及 first 到 second 新增，倒序比较产生对应删除而无新增告警。另验证别名、别名程序中局部编号变化、重复调用、共现负例、自环、断裂引用、入口不同、缺文件、损坏 JSON 及部分分析。Windows 项目环境实际执行 python -m pytest -q tests/unit/test_trust_diff.py（6 通过）、python -m pytest -q（125 通过）、ruff check .（通过）。未运行外部评价。当前范围不含跨包调用契约或论文 §4.3 的跨包 dead-end 处理，不估计检测性能。阶段实现提交人工审查，停在 P09。

## 独立审查后的接口说明

原六项测试覆盖别名程序的编号变化与自环。本轮另测同一快照的节点和边数组分别反序、两对象有向环，以及每条见证在当前排列下的重放。一个域对只保留一个存在性见证，边顺序可能影响共同对象和路径；这些编号只能在本侧解释。进程内返回值的证据由各侧独立持有。

在两侧完整且可比时，空 added 仅表示没有新增跨域对。域内改方法、改字面量及增加未使用导入都可能保持域对集合。消费结果时同时读取 status、两侧覆盖和 import_assumptions、alerts 及 unresolved_before/after。退出 0 时可以有新增候选；退出 1 时若旧侧完整而新侧已观察到新流，仍可有候选，旧侧独有流则留为未决。结果与限制见本次复核记录。[P09 审查响应](../reviews/P09_review_response.md)
