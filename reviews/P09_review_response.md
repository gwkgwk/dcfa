# P09 独立审查响应

## 修前基线与计划

main，28e07ea02153ac8c4101f55039c4a9a9723fb5f1。审查与当前 HEAD 相同，修前实现和原测试的 SHA256 分别为 f3bda426c0e19b9f914ca3409a32f03cec2aa448634af39da3f8aadd3d58b70d、82d6d262152783126932c7d03b82ca6cded4c75bf46f9a116cde6fcbde7d4ef0，与审查逐字节一致。修前 pytest 全套 125 passed。Windows、Python 3.14.0a5、pytest 9.2.0、Ruff 0.17.6；P09 运行只需标准库，无模型、阈值或深度截断。

当前提交只固定设计。git status 有既存 P07/P08 文档、P07 复现物、来源清单修改，以及未跟踪的实验日志、前置审查、P08/P09 实现、报告与测试。允许修改范围限定于 trust_diff.py、P09 报告、新增回归测试和本响应。既有原测试、冻结模块、审查报告与外部评价材料不参与修复。

N01 计划在返回证据处复制所有借用的可变 JSON 字段；验收为输入和两个输出侧的深层修改相互隔离。N02 只核实 Git 树，入库由维护者决定。N03 先用独立集合迭代参照、小环、节点和边置换、路径重放验证原算法，再修正覆盖描述。S01–03 通过接口说明和正负例验证，避免把域对、执行状态和见证编号误当语义对齐。本轮无 Critical 或 Major。

## 逐项响应及验证

|问题|等级|判断|核实依据与根因|处理与验收|状态|
|---|---|---|---|---|---|
|N01|Minor|ACCEPTED|extract 直接返回了输入的四个可变字段；同一快照作两侧时甚至可同时改写两个版本的证据|在发布结果时分别深复制节点、边、诊断及未进入函数记录。变更输入嵌套字典和清空输出某一侧列表均不能污染其他侧。闭包和路径计算继续使用本次输入的边序|FIXED|
|N02|Minor|ACCEPTED|git ls-tree -r --name-only HEAD 对实现、原测试、报告三个路径无输出；工作区能运行并不证明设计提交可重建|维护者批准归档后需在干净检出重跑。当前指令禁止提交或推送，该项仍开放|DEFERRED|
|N03|Minor|ACCEPTED|原测试只有自环；改变源程序所得的新编号未实际置换同一图。审查认定这是覆盖和表述缺口，修前参照测试也通过|补两种边的多节点环、四种顺序组合、独立不动点参照及每版路径重放，改正原报告覆盖说明|FIXED|
|S01|Suggestion|ACCEPTED|相等键仅为有向域对；成员、字面量或孤立根均不在键内|报告说明空 added 的前提；测试域内改名、值变化、孤立导入及非根标签负例|FIXED|
|S02|Suggestion|ACCEPTED|候选依赖旧侧完整与新侧正见证；总状态还依赖新侧完整|在完整与部分版本上分别测试 CLI 0/1 与相同候选并存，并核对旧侧独有流在部分情形留为未决|FIXED|
|S03|Suggestion|ACCEPTED|BFS 父指针由首次发现决定；公式只要求存在共同对象|说明见证的版本局部性；集合预期与逐边重放分开断言。未新增跨版本见证匹配|FIXED|

## 理论及测量

按 §4.3，对不同域 a、b，当从 a 根沿 data_flow 可达的对象和从 b 根沿 owns 可达的对象有交集时计入 (a,b)。§4.4 的前后集合差在此只触发候选告警；§5 的局部值归一化在两侧相同。独立参照从根出发对整张边表迭代至集合不再增长，不调用实现的闭包、父指针或见证函数。环测试还手写期望的唯一跨域方向 b→a。理论不要求见证对象在重排后唯一。[作者论文 §4.3–5](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF)

|问题|测试及预期|修前实测|修后实测及变体|
|---|---|---|---|
|N01|test_owned_evidence；后续改写不影响已返回版本证据|四例各在修改输入记录的 line 后失败|四例通过；同源双侧再修改 before 也不会影响 after 或输入|
|N03/S03|test_cycles_permutations_and_witnesses；集合与独立参照相同、两条有向路径落到共同对象|通过，说明缺口在持久回归覆盖|通过；nodes 和 edges 分别保持、反序，覆盖 owns 和 data_flow 双节点环|
|S01|test_nonroot_labels_and_domain_granularity；域对相同但未使用导入仍留在假设表|通过|通过，额外构造的 result 来源标签没有成为根|
|S02|test_cli_positive_witness_and_completion；文件位置可重放，退出状态与候选分别解释|两例通过|两例通过；真实目录经 P08 静态读取、跨文件调用、P09 CLI 到 helper.py 第 3 行，部分新侧没有产生虚假删除|
|N02|干净检出运行实现|HEAD 无对应路径|NOT_RUN，维护者归档后复核|

|命令（项目 .venv/Scripts）|结果与退出状态|
|---|---|
|python -m pytest -q tests/unit/test_p09_review.py|修前 4 失败、4 通过、0 跳过，退出 1；修后 8 通过，退出 0|
|python -m pytest -q tests/unit/test_trust_diff.py|修后 6 通过，退出 0|
|python -m pytest -q --ignore=tests/unit/test_trust_diff.py --ignore=tests/unit/test_p09_review.py|P00–P08 回归 119 通过，退出 0|
|python -m pytest -q|原套件 125 通过；修后 133 通过，均 0 失败、0 跳过、退出 0|
|ruff check .；ruff format --check src tests；git diff --check|均退出 0；Git 默认 diff 检查已跟踪内容，未跟踪 Python 文件由 Ruff、pytest 检查|
|类型、性能、Python 3.10|NOT_RUN；项目无类型门禁，本轮未测大图性能|
|风险状态、策略违规、因果归因及实体对齐|不适用，本基线无相应模块|

## 前后差异、边界与交付

Critical 0→0，Major 0→0；三项 Minor 中两项完成，一项保留。核心算法、配置、规范化键、搜索终止条件、未知门控及接口字段均未调整。修前域对与路径在本轮参照图上已正确；修后证据的生命周期与调用方输入独立。若深复制超出递归限制，compare 将该侧列为 invalid。复制成本随所复制的证据大小增长，未作性能不变承诺。P08 生产者摘要与终审一致，无需重验前置算法；前置读取失败、未知、条件根的解释继续遵循原接口。无冻结评价集参与。

修改 src/dcfa/trust_diff.py、docs/P09-report.md；新增 tests/unit/test_p09_review.py、本响应。删除文件 0。需要人工确认的是 N02 的归档版本；未提交未推送。二审重点为双侧复用同一输入时的嵌套证据隔离、多节点环的方向性、重排后的本侧证据下标、未决结果与候选并存。P10 保持暂停。

**READY_FOR_REVIEW**
