# 阶段一表示能力覆盖矩阵

“论文支持”指 KnotScryer v1 对研究概念有明确描述。P01 未定位到可确认的官方实现；下表不主张与原程序逐例一致。SCS 概念定位于 §III-B，内部图定位于 §III-C、算法 1 第 3–5 行。具体句式、调用点、局部连边与原件重放依据 P03、P04、P05 契约。[P01 审计](reproduction/knotscryer_analysis.md)

| 类别／用例 | 人工语义预期 | 实际观察 | 依据与判定 |
|---|---|---|---|
| 自然语言 N1 | Accept text. 表达消费文本 | Text 输入端口通过 possible reads 边指向 accept | §III-B 端口、§III-C reads；识别句式和逐边证据为适配。有限支持 |
| 程序操作 P1 | polish(item) 有一个实参，不证明入口或执行 | call_expression 收录 polish，参数为 item；operand 为 static | §III-B 提及脚本扫描；语法操作数和调用类型为扩展。支持调用语法 |
| 工具 T1 | 调用点与模拟绑定共同支持可能调用 | stamp → mock-stamp，may_invoke 为 possible | P04 显式绑定扩展。条件支持 |
| 工具 T2 | 移除绑定后，名为 stamp 的调用不足以指认工具 | 调用仍存在，无 may_invoke，保留 tool_binding_unresolved | P04 扩展。负对照符合 |
| 依赖 D1 | make() 的结果占据 wrap 的实参槽 | result_to_operand 为 possible，operand 为 static | §III-C 支持内部关系；嵌套 AST 槽位规则为 P04 扩展。局部支持 |
| 依赖 D2 | v=make() 后 wrap(v)，人工可推出经 v 的定义使用关系 | 两个调用和参数 v 均存在，图止于 v → wrap | 当前无法表示跨语句 def-use |
| 条件 C1 | stamp() 的分支前提是 enabled 为真 | 提取了调用，图中没有谓词、控制依赖边或执行观测 | 当前无法表示一般执行条件 |
| 执行约束 C2 | 声明 write 需要授权 | SCS 的 requires_authorization 为 true，图保留效果节点；无执行边 | §III-B 效果属性。支持声明；未验证授权门实际生效 |
| 安全效果 E1 | 发送 URL 的指令可能产生向外发送效果 | send 动作与 send 效果之间有 possible may_cause 边，同时保留目标上下文和边界 | §III-B/C 效果和边界；逐句归属与 may_cause 为 P04 扩展。有限支持 |
| 多文件 M1 | 同一工具边同时依赖调用源码和外部声明 | 正向索引在 skill/logic.py 与 analyst/bindings.json 均命中同一边，映射 verified | §III-B 逐项证据；双来源边及验证为 P05 扩展。支持此类多文件证据 |
| 未知 U1 | 未解释的文字不构成已知能力 | 无能力主张或语义边，存在 uninterpreted_instruction | 项目缺证契约。保守表示 |
| 稳定性 S1 | 无关说明改写并移至指令前，输入能力及内部关系保持一致 | 两个快照独立匹配同一人工预期，能力节点及带方向、确定性的语义边多重集相等 | 项目测试的变形性质。仅在所列变换和比较范围内成立 |

未知状态和可能边均不能充当风险标签。这里的十二项是预先选择的语义断言，无法用于估算真实样本的覆盖比例。
