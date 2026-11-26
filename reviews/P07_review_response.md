# P07 独立审查响应

## 修复前登记与设计

main，d133e941b6bc8d606beede4280ee87ce84c84079，与审查 HEAD 相同。设计 d0f4dd9。开始时无已跟踪修改；未跟踪 esprima_logger.log、evaluation.ndjson、run_log.log 及七份 P03（三轮）、P04、P05、P06、P07 独立审查报告。原审查报告记录的工作区状态早于这些运行日志。全部保留。修改范围为 P07 复现驱动、合成输入、发布图、复核脚本、P07 专项测试、两份 P07 文档、本响应及 P00 既有登记机制的数据条目。冻结模块、原始分析器和评价数据不参与修复。

## 核实与修复计划（实现前）

| 编号 | 等级 | 核实 | 证据及根因 | 方案、验收及影响 |
|---|---|---|---|---|
| M01 | Major | ACCEPTED | 旧驱动仅构造顶层语句；历史 pair2 仍保留两份函数体入口，results 单独无法还原输入 | 恢复实际字节，两个显式夹具共用构造入口，独立重跑并对照。影响负观察的可追溯性 |
| N01 | Minor | ACCEPTED | 在临时图同时修改 literal 和翻转函数返回边，旧检查退出 0。节点存在不能证明有向可达 | 依照两份输入分别核对实参、模块、方法、返回对象及有向类型边；测试单独破坏证据和重编号 |
| N02 | Minor | ACCEPTED | 预检的“当前运行结果”描述了确认 SHA 前的状态 | 给历史段落加时点、链接最终状态并测试链接 |
| N03 | Minor | ACCEPTED | 两张 after 图各含三处本机入口路径，涉及不同 XML 键；路径来自上游文件入口 | 仅在发布层重写与输入入口完全相同的值，保留图关系及上游原件的 Git 追溯；换运行目录复核 |
| S01 | Suggestion | PARTIALLY_ACCEPTED | 已有报告限制意图推断；上游先归一化再过滤，函数的非空返回证实候选变化 | 在本阶段交付说明解释差异；P08 设计延后 |
| 来源登记（§19） | Suggestion | ACCEPTED | 文档存有 SHA，实际 P00 清单为空 | 使用既有 schema，核对论文文件摘要、仓库 SHA 和 pin 来源，跑项目登记校验 |

这些问题影响研究证据的复核与后续引用。计划保留两个版本顺序、冻结接口和原方法，修复不依赖外部数据。对照预期为函数体两版关系及差分为空，顶层样例有两支路径汇入同一返回对象；后者的编号可变化。Windows 包对入口预期仍可能失败，须保存真实结果。

## 处理结果与反例验证

| 问题 | 状态 | 测试名称与理论预期 | 修复前 | 修复后及变体 |
|---|---|---|---|---|
| M01 | FIXED | recovered_function_body_bytes、archived_and_repeated_records；从真实入口重建空关系 | 只有顶层生成器，函数体文本缺失 | 原 pair2 两文件 SHA-256 与夹具一致；新目录两版关系和差分均为空，过滤前图规模 586/491、834/1363；顶层对照仍非空 |
| N01 | FIXED | invalid_witness_fails；缺失有向边或对象语义应拒绝 | 临时图改 literal 并反转返回边后仍退出 0；单独变体修前 NOT_RUN | 分别修改代码、方法名、边类型、方向、删除边、换终点均被拒绝；缺文件报错。重跑方法节点由 1741 变为 1726，真实见证仍通过 |
| N02 | FIXED | preflight_identifies_history_and_final_report | 原标题为当前状态 | 预检与最终结果有时间及链接，检查通过 |
| N03 | FIXED | portability_only_rewrites_exact_entry、archived_and_repeated_records | 两份 after 图均含本机路径 | 发布副本使用版本目录相对入口；含空格和 & 的目录、相近但不同的字符串、两次真实运行均验证 |
| S01 | DEFERRED | 无害顶层输入原始函数返回非空 | 记录已有非空差分，无恶意标签 | P07 交付文档补充 §4.4 与实现切片的区别。涉及 P08 的工作留待人工决定 |
| 来源登记 | FIXED | confirmed_upstream_in_registry | 清单 0 项 | 实取作者 PDF 并计算摘要；既有 check-sources 接受 1 项。P02 记录仍缺失，不能证明该 SHA 是论文发布标签 |

## 执行记录

项目命令使用 Windows 的 .venv/Scripts/python.exe（3.14.0a5）和 Ruff 0.17.6。实验命令用设计中的独立 Python 3.10.9 环境。Git 验证上游 HEAD 与登记一致；原临时归档 selected.zip 的 94 个文件及 init.zip 的 1 个文件与实际源码树逐字节相同。

| 命令 | 修前 | 修后 |
|---|---|---|
| python -m pytest -q | 91 通过，退出 0 | 104 通过，0 失败，0 跳过，退出 0 |
| python -m pytest --ignore=tests/unit/test_p07_review.py -q | 同原全套 | 91 通过，退出 0 |
| python -m pytest tests/unit/test_p07_review.py -q | NOT_RUN，新文件 | 13 通过，退出 0 |
| python reproduction/P07/check_record.py | 退出 0，破坏图的副本也误通过 | 默认及 --case function-body 分别退出 0 |
| ruff check .；ruff format --check . | lint 0；格式检查报告 2 个文件需格式化 | 均退出 0 |
| dcfa check-sources；git diff --check | NOT_RUN | 均退出 0 |
| 类型检查、大规模性能 | NOT_RUN | NOT_RUN；无配置的类型检查器，本次未测性能 |
| P06 → P07 端到端 | 不适用 | 不适用；P07 接收独立 JS 包对，P03–P06 单快照接口不在调用链 |

实际实验对 function-body 和 top-level 分别在新的临时工作目录执行以下命令。完整 stdout/stderr、原函数 JSON 和对应发布图保存在 reproduction/P07/recheck/。每个包对命令退出 1，没有原生结果文件；两个 probe 和随后两个 check 分别退出 0。

~~~text
python run_pair.py <固定源码> <新输入目录> --case <case>
python probe_modules.py <固定源码> <新输入目录> <新输出目录>
python check_record.py <新输出目录> --case <case>
~~~

## 修复前后影响及交付

Critical 0→0，确认的 Major 1→0 待修、Minor 3→0 待修。原始算法、语义表示、前置接口没有变更。差分仍为顶层新增 (:local, path)、函数体为空；证据由只查编号改为核对对象身份和有向属性边。附加文件缺失会报错。没有引入不确定性分类、语义对齐或风险策略。论文 §4.2–4.4 及固定源码 fast/dataflow/trust_domains.py 的 flagged_single_local_rels_from_tuples 为解释依据。[作者论文](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF)

修改 docs/P07-preflight.md、docs/P07-report.md、third_party/sources.json、P07 的 run_pair.py、probe_modules.py、check_record.py 和两份历史 after.graphml。新增 portable_graph.py、inputs/ 两组合成入口与行尾声明、recheck/ 两组运行证据、tests/unit/test_p07_review.py 及本响应。删除文件 0。包对驱动增加可选 --case；校验器可传目录与 --case；文件模式的三个位置参数不变。

历史 npm 安装参数缺少独立日志佐证，本轮没有重新安装。Windows 原生包对仍在 mem_info 读取 shared 时失败。上游 197–198 行依据两个空 file_node_nums 打印警告；文件模式在该字段为空时仍有 AST 和见证，故仅凭警告无法确定文件选择根因。包对失败保留为失败。无 P00—P06 缺陷需要重开验收，未发现独立 P02 验收材料。P07 仍是部分复现。

**READY_FOR_REVIEW**。请二审复查恢复的输入字节、路径替换的字段范围、同一返回对象的两支有向证据及包对原生日志。部分复现能否被项目接受由人工确认。工作区未提交，P08 尚未启动。
