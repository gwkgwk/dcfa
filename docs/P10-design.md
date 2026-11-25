# P10 基线独立验证设计

以用户启动 P10 为阶段授权。工作区有 P09 独立审查及修复响应，未发现单独的 P09 终审文件。本阶段独立检验工作区中修复后的 P08/P09，不代签该审查。

同一合成 Skill 入口 main.py，仅静态读取；对比有向域对、两侧流集、差分、候选、未知项与完成状态。人工 oracle 在首次运行前固定；默认 SKILL.md 为 synthetic，未指定 after 源码时复制 before。L 为 :local→import:api，AB 为 import:a→import:b。所有未列出的域对集合为空。candidate 集与 added 相同。“合法”指人工设计的功能场景，不是基线预测。独立判据来自 RogueOne §4.3 两类闭包相交与 §4.4 集合差，以及 P08 的停止规则；不从分析器输出生成 oracle。[作者论文](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF)

冻结范围为显式入口的 P08 解释器、P09 比较器、已跟踪安全读取器及其配置、基线专项回归和本阶段记录。单 :local，所有边 may，入口相同，未核验导入按声明建模；无模型或调参。设计和 oracle 先提交，再对工作区和冻结提交的干净导出运行。排除其他阶段未提交工作、外部数据及运行日志。
