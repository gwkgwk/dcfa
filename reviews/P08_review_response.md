# P08 审查修复设计与响应

基线 main / 48c0d52025938be7f5c74dfcd9d712793572662c；该提交仅固定设计。未跟踪实现和原测试的 SHA256 分别为 3C15E0107CBA0CA06F7B1EC3DAA326B6CA7DBDBDC1A2B4123C1F7649C6030CAC、1493C8EBA6E0ADD4B03ABB7DC5BE79245507F423A1C54EBABEC316D424CA9BF7。审查未提供文件摘要，因此用同一 HEAD、源代码路径与反例再次核实。工作区已有 P07 文档、复现脚本与图、来源登记、实验日志、历轮审查、P08 报告、实现及测试的未提交内容。本轮仅修改 P08 实现和文档，另建独立测试与本响应。Windows，Python 3.14.0a5、pytest 9.2.0、Ruff 0.17.6、PyYAML 6.0.4、fastjsonschema 2.22.3；AST 后端无模型配置。对象上限 4096，调用深度 24。

## 实现前计划

M01/M02 统一模块根、成员查找及外部调用的建边规则，按父对象和成员名复用身份，文件绑定方法保留接收者。M03 使用快照内包证据，并标明未核验的导入假设。N01/N04 细分受限词法环境诊断；N02 明确可达范围；N03 放行首条文档字符串；N05 显示入口分析状态；N06 统一定义证据；S02 统一空操作。N07 须由维护者决定提交。各性质先在临时合成目录测试，比较语法变体及独立负例，保持原有公开入口、读取器和阶段边界。

## 逐项响应、根因及回归记录

下表的测试名省略 test_ 前缀。新测试在旧实现上实际运行 12 个参数化实例，退出 1，全部失败。某个实例首个断言失败时，不把其后尚未执行的断言算作修前实测。原代码也分别核对过对应分支。

|编号|等级|核实结论|修前证据及根因|修复行为、预期及变体验证|状态|
|---|---|---|---|---|---|
|M01|Major|ACCEPTED|from 直接建 API，未建模块；普通属性每次新建|member_identity_and_edge_rules 分别测试普通导入和 from 别名，同一成员复用，模块到成员的两类边均存在|FIXED|
|M02|Major|ACCEPTED|属性仅 owns，调用仅 data_flow，句柄没有隐式实参；旧 receiver_and_flow_path 两例均失败|补检索的 data_flow、调用的 owns 及绑定句柄到结果的 may 流。直接与提取方法调用都能从路径到达 send，不能到同现的 other；独立断言直接接收者边。裸域字符串不参与可达验证|FIXED|
|M03|Major|PARTIALLY_ACCEPTED|旧 package_and_library 遇同名本地包却无诊断。缺单文件不能推出真实外部根|识别普通包并中止；外部根写 resolution，标准库名称与其他声明区分。缺乏安装证据时拼写错误与真实第三方名字无法可靠区分，均保持未核验。无宿主依赖探测|FIXED|
|N01|Minor|ACCEPTED|函数内自由 open 由通用未解析分支中止|scoped_uncertainty 给专门诊断；显式传入句柄可解析其成员。保持自由变量边界，避免误认被遮蔽的内建函数|FIXED|
|N02|Minor|PARTIALLY_ACCEPTED|不遍历未调用体符合显式入口设计；缺少覆盖信息|scope_and_noop 断言仅 unused 出现在未进入清单，函数体内未解析表达式不被执行或推断|FIXED|
|N03|Minor|ACCEPTED|旧跨文件导入把首条字符串算作初始化|docstring_definitions_and_initialization 允许首条字符串；同一模块加赋值仍 partial。不放开一般初始化|FIXED|
|N04|Minor|PARTIALLY_ACCEPTED|自名引用先报名字未解析；函数参数递归原为通用 unsupported_call。前者不能仅凭拼写证明实际递归|scoped_uncertainty 对未解析自名与实际活动函数对象再次调用分别测试|FIXED|
|N05|Minor|PARTIALLY_ACCEPTED|读诊断阻止解释合理；空图缺入口运行标记|read_block 在邻居超预算时保留 byte_limit 且入口 not_started。运行中断和成功分别为 incomplete、finished|FIXED|
|N06|Minor|ACCEPTED|函数定义和导入只写环境，遗漏绑定表|统一 define；docstring_definitions_and_initialization 检查本地函数和导入别名的 definition，保留对象引用及出现位置|FIXED|
|N07|Minor|ACCEPTED|git status 与设计提交确认实现未入库|用户明确禁止提交；报告给出基线摘要与可复核工作区。须由维护者归档并从干净检出重测|DEFERRED|
|S01|Suggestion|ACCEPTED|边无运行确定性字段，原设计仅称可能依赖|修订模式说明统一规定所有 data_flow 为 may，避免引入逐边不同解释；无运行时确认|FIXED|
|S02|Suggestion|ACCEPTED|pass 中止、独立省略号表达式造额外常量|scope_and_noop 的两个函数体变体都正常返回且不造 Ellipsis 节点；作为值使用的省略号保持常量语义|FIXED|
|S03|Suggestion|PARTIALLY_ACCEPTED|P08 不调用 P07 差分；没有观察到继承恶意标签的代码路径|确认 P07 的非空差分只能作候选关系。后续设计若引用需重申，P09 由负责人另行授权|DEFERRED|

## 依据、影响与边界

P07 最终验收覆盖固定 JS 文件模式。P08 只依赖 P03 使用的有界 scan，前置 SCS、图、证据索引及 P07 JSON 均无输入接口。无需解冻前置模块。属性检索复用已有子对象、首次创建的两类边、外部调用的控制与可能依赖边，分别依据 §4.2(2)(4)。图 4 的隐式接收者在 Python 中落实于绑定文件方法。模块函数采用 Python 调用约定。规则及 scope 定义见修订的 docs/P08-design.md。[作者论文](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF)

核心变化为原先断裂的可达路径及重复成员身份；来源标签依然是构造标签。属性赋值、一般动态分派、模块执行不在子集内。静态影响可达不证明文件内容已经读取或披露。跨版本匹配、差分、风险状态和归因均不适用。无阈值修改或外部样本输入。公开入口签名、旧 JSON 主字段和 CLI 成功/失败约定保持兼容；成员复用将改变局部 ID 和图规模，消费者应按对象引用取证。新版增加 entry_analysis、unvisited_functions、根节点 resolution，补齐定义绑定。发现普通包、词法名字不能确认或读取失败时保留诊断。

## 命令、实测和修复前后对照

均用项目 .venv/Scripts 中的工具。测试命令中的 python 和 ruff 分别指该环境可执行文件。

|命令或项目|修前|修后|
|---|---|---|
|python -m pytest -q|107 通过，0 失败/跳过，退出 0|119 通过，0 失败/跳过，退出 0|
|python -m pytest -q tests/unit/test_p08_review.py|0 通过、12 失败、0 跳过，退出 1|12 通过，退出 0|
|python -m pytest -q tests/unit/test_program_flow.py|含在原全套|3 通过，退出 0|
|python -m pytest -q --ignore=tests/unit/test_p08_review.py --ignore=tests/unit/test_program_flow.py|含在原全套|104 通过，退出 0；包括 P00—P07 回归|
|python -m dcfa.program_flow DIRECTORY entry.py|本轮 CLI 基线 NOT_RUN|真实临时 Skill，入口从 tools 导入 report，传入 open('spec').read()；退出 0、finished、13 边。换为 if True: pass，退出 1、incomplete、0 边。两次仅解析文件|
|ruff check .；ruff format --check src tests；git diff --check|本轮修前 NOT_RUN|均退出 0；git diff 默认只检查已跟踪变更。全仓 ruff format --check . 退出 1，独立审查 Markdown 中示例格式不合规，原报告保留|
|类型检查、性能、Python 3.10|NOT_RUN|NOT_RUN。未配置类型门禁，未测运行性能，不推断性能提升|
|P07 至 P08 数据接口、跨版本、闭包与策略测试|不适用|不适用。端到端以真实目录→scan→AST→CLI JSON 为准|

Critical 0→0；三条 Major 的可修正行为均有针对性验证。七条 Minor 中六条落实，第七条待人工版本归档。修改 program_flow.py、P08 设计及 P08 报告；新增 test_p08_review.py 和本响应。没有删除文件或修改原测试预期。报告不替代独立验收。

**READY_FOR_REVIEW**。二审请重点复核同一父对象下的别名复用、不同接收者的隔离、无关调用不可达、局部包与未核验外部声明的区别，以及部分图的入口状态。N07 的干净提交复现须人工确认归档后执行。P09 保持暂停。
