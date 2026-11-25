# P03 独立审查逐项回应

**交第二轮独立审查。** 审查输入为 [原报告](P03_independent_review.md)，SHA-256 为 `18cc836a1ee672d43aa7dd36e4e32b734a6c05b72818a26230baaffd2b035524`。对照提交 5157a4b，先在 589bc42 提交修订契约，再于 986aa61 提交实现与测试。16 项中 10 项 ACCEPTED、6 项 PARTIALLY_ACCEPTED。原报告没有列出 Critical。P03-4 所建议的字段赋值未采纳，请第二轮重点审核。

研究目的仍为从单个静态快照提取带证据的 SCS。依据为原论文 §III-B 及 [P01 的逐节审计](../docs/reproduction/knotscryer_analysis.md)。论文提供信息类别；本项目负责本地文法、证据强度与序列化契约。本次仅用合成输入、代码和来源记录核实意见。论文“官方源码不存在”的断言超出证据，P01 的结论限于检索当日未定位到可确认的公开官方版本。

## 逐项判定

表中函数均可在提交 986aa61 的 src/dcfa 下定位，测试名称均指 [新增反例集](../tests/unit/test_p03_review.py)，原有测试原样保留。

| 项目 | 判定 | 原因、修复与实际影响 | 回归证据 |
|---|---|---|---|
| P03-1 Major | ACCEPTED | Material.document 先前直接跳过所有 # 开头行。现先识别示例，再对 ATX 标题移除标记、沿用原文法。符合句式的标题保留原行证据，其余标题生成定位诊断。 | test_heading 同时检查标题 Code 与正文 URL |
| P03-2 Major | ACCEPTED | strip 抹去了区分示例的前导空白。现在先检测缩进，四列及以上的非空文本进入示例诊断。这是保守的 Markdown 子集，复杂列表缩进也可能进入未知。 | test_indented_example 覆盖空格及制表符；test_indented_delimiter_remains_example 覆盖缩进分隔符 |
| P03-3 Major | ACCEPTED | YAML 分支原先先发端口、再报形状错误。现在仅在存在非空类型时发出端口主张；序列、空映射、空标量均留下诊断。直接证据分值仍表示可见声明。 | test_invalid_port 三种材料均无端口 |
| P03-4 Major | PARTIALLY_ACCEPTED | 接受端口未保存显式发送起点。拒绝把 from local/workspace 一律赋给 trust_origin。§III-B 将数据的信任来源、暴露范围、跨域关系分列。本地可以暂存第三方生成的数据，发送起点本身不能判定数据来源。Material.document 现在将起点同时记录于端口 transfer_source 与边界 source；缺少信任来源证据时 trust_origin 仍为 null，显式 YAML trust_origin 仍按证据保存。 | test_origin_semantics 在同一快照区分显式 ThirdParty、发送起点 workspace 和未知的输出来源；原 test_transfer_instruction 未改 |
| P03-5 Major | ACCEPTED | 根文档已通过 lstat，而 entry_limit 会在处理该目录前终止；旧 extract 又根据未收到文本追加笼统的文档不可用诊断。移除这一重复归因，保留读取器的实际原因。预算截止仍可导致 failed 和空类别诊断；没有提高预算或宣称已读取正文。 | test_entry_limit 使用 257 项实际目录 |
| P03-6 Major | ACCEPTED | scandir 和普通 open 只能覆盖默认流。新增 windows_streams.has_named_stream 查询 Win32 流元数据，命名流记 unknown，枚举出错记 read_failure；不读取流内容。拒绝链接／重解析点的原边界保留。 | test_named_stream 在 Windows 上实际创建附加流，检查路径、状态及合成标记未泄入输出 |
| P03-7 Major | PARTIALLY_ACCEPTED | 接受原测试缺少独立反例、CLI 对照自身无法证明内容、缺少提交样例回归。关于原 trust_origin 断言错误的说法，同 P03-4。新增反例与落盘 JSON 比较；没有删除或改写任何原断言。 | test_golden 读取 examples/p03-scs.json；反例红绿结果见下 |
| P03-8 Major | ACCEPTED | 旧 README 安装路径在 Windows 3.14.0a5 可取得面向稳定 cp314 的原生 wheel；P03 原运行已观察导入崩溃。修订 README，由 scripts/install_dev.py 在该早期 ABI 安装依赖前选定 PyYAML 6.0.4 纯 Python 构建，安装后新进程隔离导入。稳定解释器沿用常规安装。跳过安装脚本在该 alpha 上直接运行 pip 仍可能选中不兼容 wheel。 | 干净 venv 首次按 README 安装，导入、53 项测试通过；test_import 用子进程核验 |
| P03-9 Major | PARTIALLY_ACCEPTED | 接受库调用与 Skill 动作混用的风险。添加强制 kind，Schema 同时约束 kind 与 evidence.method；调用表达式和指令动作可以分别筛选。单有 def render 也不能证明该函数向 Agent 暴露，未将其升级为入口。旧调用证据保留；使用者须先按 kind 区分。 | test_operation_kinds_and_order；test_schema_disallows_python_as_instruction 验证错误类型被拒绝 |
| P03-10 Minor | ACCEPTED | 边界分支只复制两个已知键。现在检查额外键，按 YAML 键节点标记定位具体行，原文片段继续保留。 | test_boundary_extra 定位第 5 行 |
| P03-11 Minor | ACCEPTED | 围栏状态缺少 EOF 处理。未闭合时在开栏行记录 unclosed_fence，不解释栏内语句。 | test_fences 分别验证闭合后恢复正文、未闭合时保持未知 |
| P03-12 Minor | ACCEPTED | 原类型表只在语言路径生效。YAML 对已有四种类型统一大小写；词表外的类型保持原字符串并诊断，片段保留原拼写。 | test_types 同时检查混合大小写、未知类型及行号 |
| P03-13 Minor | PARTIALLY_ACCEPTED | 接受读入失败和一般语义缺口折叠。成功取得文档后，存在 read_failure 时顶层使用 partial_read，其余诊断使用 partial；必需文档未取得仍为 failed。空类别保留缺证诊断；在这个有限抽取器中，空数组不能证明无此能力。退出码 1 仅表示工程结果不完整或失败，禁止用于风险统计。 | test_partial_read_and_inventory；原 test_required_document_and_schema |
| P03-14 Suggestion | PARTIALLY_ACCEPTED | 原契约无顺序保证，不能据此认定旧结果算法错误。接受确定性源码顺序建议；调用按起始行、列及结束位置排列。数组序号没有跨版本身份或执行先后含义。 | test_operation_kinds_and_order 将函数内较早调用与顶层较晚调用作对照 |
| P03-15 Suggestion | PARTIALLY_ACCEPTED | role 表示材料角色，保留原分类；接受仅看文件清单难知处理状态的问题。新增 processing：processed 表示已送入解释流程，parse_failed、unread、inventory_only 分别表达解析失败、未读和仅登记。具体语义缺口仍查看 diagnostics。 | test_role_and_processing_are_independent；test_partial_read_and_inventory |
| P03-16 Suggestion | ACCEPTED | 源码可证校验器曾逐次编译；异常出口问题属于故障注入场景。现按进程缓存校验器，CLI 在输出边界校验，Schema／资源等契约错误返回独立的失败 JSON 和退出码 1。该错误封装不冒充正常 SCS。 | test_validator_failure 注入空字典；test_schema_disallows_python_as_instruction 检查缓存复用 |

## 差异、接口与实际影响

运行 `git diff 5157a4b 986aa61` 可检查全部修复，涉及 10 个文件，新增 412 行、删除 24 行。设计在 docs/P03-design.md，读入改动在 skill_reader.py 与 windows_streams.py，提取和校验改动在 scs.py、scs.schema.json、cli.py，安装入口在 README.md 与 scripts/install_dev.py，回归和独立输出分别在 tests/unit/test_p03_review.py 与 examples/p03-scs.json。旧测试文件没有差异。

`extract(Path)` 和 `dcfa scs DIRECTORY` 仍只接收一个快照。输出版本从 p03.1 升至 p03.2，旧版严格 Schema 与新版新增字段不兼容。示例仍为 4 个端口、3 条操作、1 个效果、1 项暴露、1 项边界。新版本补充文件处理状态、操作类型与传输起点字段；原示例标题产生一条未知诊断，故诊断从 3 条增至 4 条。输出仍为 partial。未添加推断未知入口、内部边或恶意意图的逻辑。

## 实测与反证

| 检查 | 实际结果 |
|---|---|
| 变更前，原环境运行 python -m pytest -q | 30 passed in 0.68s |
| 将 5157a4b 的 src 归档到临时目录，优先从该目录导入；运行最终 test_p03_review.py | 19 failed, 4 passed in 1.25s。这里包含新版接口、Schema 与更新的样例预期，不能解释为 19 个相互独立的旧缺陷 |
| 原纯 Python PyYAML 环境，python -m pytest -q | 53 passed in 1.01s |
| 干净 Windows 3.14.0a5 venv，python scripts/install_dev.py，随后 python -m pytest -q | 53 passed in 1.01s；隔离导入成功，PyYAML 6.0.4 的 __with_libyaml__ 为 False |
| 独立 Python 3.10.9 环境，python -m pytest -q | 53 passed in 0.91s |
| 单跑 P00 的 test_registry、test_runs、test_cli、test_fixtures；dcfa check-sources | 18 passed in 0.28s；清单校验退出 0，登记数 0 |
| P01 来源回归 | 校验本地固定版 PDF 字节数和 SHA-256 与 manifest 一致；11 个去重后的论文 HTML 章节锚点全部存在 |
| ruff check . / ruff format --check . | All checks passed；31 files already formatted |
| 干净环境构建 wheel 并打开归档，运行已安装的 dcfa scs | wheel 含 p03.2 Schema 和 Windows 流查询模块；CLI 退出 1，实际 JSON 与提交的样例逐字段一致 |

第 8 节中的围栏、硬链接、junction、标签拒绝、脚本不执行、token 预算和重复提取均在全套测试中覆盖。真实 ADS 探针先写默认流再写命名流；直接重写默认流会使探针不能可靠保留命名流。多文档 YAML 和带括号的属性调用另有回归。审查列出的 POSIX 大小写、不同文件系统的流枚举行为及无权限创建的文件符号链接，本轮没有跨平台实测。对源码不可达与运行时权限的边界仍以 P01 和 P03 设计为准。

**阶段判定：** 本轮修复、针对性回归及前置回归已完成。审查员原评分是历史记录；本回应不重新打分或代为批准。修订契约与 P03-4 的处理等待独立二审和人工确认。P04 尚未启动。
