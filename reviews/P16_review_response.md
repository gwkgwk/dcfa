# P16 独立审查修复响应

**READY_FOR_REVIEW**。范围为 P16 编排、失败诊断所有权、仓库回归测试和阶段状态。会话中负责人给出了原始任务；仓库中无单独的正式任务书。设计与伪代码见 docs/P16-design.md，本轮补齐 docs/P16-report.md。

## 版本与验收证据

main，HEAD ed9238402f67d456983894cc79659ac8533f5b8a，无本轮提交。修复前逐项比对候选清单，实际为 19 条，19/19 一致，独立报告称 18 条。P16 实现、测试和四份原有阶段工件未跟踪。git status 另显示 11 项既有已跟踪差异（P07、P10、P12 文档、P07 复现、P10 测试和来源清单），还有其他阶段未跟踪代码、测试、审查记录及运行产物。保留原工作树。未修改上游算法或独立审查原文。

|编号|等级|核实结论|依据、根因|修复与验收条件|状态|
|---|---|---|---|---|---|
|N01|Minor|ACCEPTED|规范末句仍称第 4、5 节未实现，与 P13、P14、P15 实际接口及 P15 终审不符。|只修订 docs/algorithm_spec.md 末尾工作树进度，列出单侧求值、有限差分、有限位置及语义关联，注明最小充分编辑集未实现。|FIXED|
|N02|Minor|ACCEPTED|HEAD 缺实现，候选校验只能验证现有文件。|待负责人授权归档，在干净检出核对指纹与复测；当前更新候选清单以供复审。|DEFERRED|
|S01|Suggestion|ACCEPTED|9 项原测试未同时锁定反向键、纯授权、跨模态证据位置与非法契约。新断言改实现前即通过，属于覆盖缺口。|tests/unit/test_update.py 新增反向键与纯授权、位移及见证文件、五组非法契约测试；以实际源行和授权集合判定。|FIXED|
|S02|Suggestion|PARTIALLY_ACCEPTED|重调会重读，但失败报告内 problems 引用了同个 SCS 诊断字典。将摘要原因改成 edited 会同步篡改原件诊断。对整个返回值执行一次 deepcopy 仍保留内部别名。|src/dcfa/update.py 的 _snapshot 在构建问题摘要时复制记录；test_failure_summary_is_independent 修改摘要后分别检查同一报告原诊断和重调结果。|FIXED|

## 真实回归

Windows、项目 .venv/Scripts/python 3.14.0a5，pytest 9.2.0、Ruff 0.17.6。所有新增输入为临时合成文本。未使用冻结评价集、真实凭据或动态 Skill 执行。

|命令与时点|退出|通过|失败|跳过|
|---|---:|---:|---:|---:|
|python -m pytest -q，修改前|0|223|0|0|
|python -m pytest -q tests/unit/test_update.py，新增测试、旧实现|1|16|1|0|
|同命令，修复后|0|17|0|0|
|python -m pytest -q --ignore=tests/unit/test_update.py|0|214|0|0|
|python -m pytest -q，最终|0|231|0|0|

S01 的相反方向分别为 introduced 和 resolved，无编辑时两条查询均无语义编辑依赖。移动后程序节点及边的位置必须全属 main.py 且旧第 1 行、新第 2 行；指令位置只属 SKILL.md 第 1 行。空配置标识、重复查询 id、不同 Skill、坏摘要、错误成员均拒绝。S02 修复前唯一失败来自同一失败报告内部的交叉写入。真实管线贯穿 P03/P04/P05/P12/P13/P14/P15。Ruff 全项目检查与 git diff --check 退出 0（后者不涵盖未跟踪文件）。按示例配置重建混合快照并执行，规范化后的完整结果与原 JSON 相等。原临时探针脚本、类型检查、动态沙箱、正式实验和性能测试 NOT_RUN，未将这些项目计入通过数。

## 剩余事项与移交

本轮更改 update.py、test_update.py、P16-design.md、规范末尾进度和 P16-freeze-candidate.json；新增阶段记录及本响应。冻结候选继续 pending_independent_review，归档前不能从 HEAD 单独复现。本次无算法定义、阈值、基线、数据标签或接口字段调整。没有外部实验结果需要重新执行。请二审重点复核内部诊断隔离、两种模态的所有重放位置、相反查询的保留、契约拒绝和候选指纹。后续阶段须由负责人决定。

## 独立 Agent 二次复核回执

独立 Agent 只读复核 N01、S01、S02，并确认 N02 待授权归档。独立命令 .venv/Scripts/python -B -m pytest -q -p no:cacheprovider tests/unit/test_update.py 得到 17 通过、0 失败、0 跳过。将真实结果中的一条见证故意换到另一文件后，新断言按预期失败。反向隔离反例在新版解析失败时清空原始 SCS 诊断，失败摘要仍保留 invalid_python，状态仍为 analysis_failed。候选文件独立复算 19/19 一致，git ls-tree HEAD src/dcfa/update.py 为空。该复核未发现阻塞问题，正式验收及归档由项目负责人决定。
