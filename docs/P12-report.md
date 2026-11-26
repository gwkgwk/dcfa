# P12 实现与验证报告

预注册提交 ed92384 固定算法设计、伪代码与预期性质。输入限定为 P11 有限且规范化的契约片段。实现和运行入口为 src/dcfa/alignment.py；测试为 tests/unit/test_alignment.py。[设计](P12-design.md) · [P11 §3](algorithm_spec.md)

## 运行与输入

运行 python -m dcfa.alignment before.json after.json，或调用 align(before, after)。每侧 JSON 的 graph 来自 P04 build_graph；index 来自 P05 build_index；contract 由分析者在 Skill 外提供。graph_sha256 取自该图的 P05 索引。两个摘要相同仅证明引用同一图表示；必须信任索引生产者、契约来源和版本归属。响应中的证书标识供追溯，不验证外部签名，也不从 Skill 自述产生授权。CLI 退出 0 表示比较已运行，可以有 unresolved；无效输入、契约冲突及不可比输入返回诊断并退出 2。

contract 最小结构示例（占位字符串由调用者按实际输入填写）：

~~~json
{
  "skill":"synthetic-preview","environment":"reviewed-v1","scope":"entry display",
  "version":"V1","graph_sha256":"<P05摘要>",
  "coverage_certificate":"inventory-1","unique_persistent_roles":[],
  "units":[{"members":["/scs/operations/0"],"certificate":"interface-spec-1",
    "role":["agent","preview","in:text","workspace","display"],"anchor":"preview-slot",
    "observations":[["requested","text","formatted","local-private-authorized"]]}]
}
~~~

版本内 members 引用 operation 或 effect；跨版本不靠该指针相等。闭包证明 coverage_certificate 断言在该 scope 内能力与允许的组合已列全，不能把普通局部提取成功标作封闭。聚合单元必须给出 aggregation_certificate 和整体观察表；不同实现片段的排列、控制与数据依赖是否满足聚合契约由外部证书负责。缺少可靠分组时应传单项并将覆盖保持开放。索引证据缺失或未附能力证书的单元在候选计算中保留未知。接口内 role 和表值是 E 内的规范符号，名称、自由文本和路径不得充当稳定绑定。

结构上下文用可选 slots 描述，例如 {"slot":"payload","edge":3,"neighbor_binding":"verified-source-role"}。edge 是该图的边下标。只有已验证且横跨本单元边界的非 contains 边用于约束；方向、关系和邻居绑定共同组成签名。slot 代表契约规定应持续的逻辑位置，缺失不构成否定。unique_persistent_roles 声明在已知不变结构限定后，双侧唯一且无其他竞争的实例应持续；仅凭候选分数或局部唯一不产生该契约。

## 判定及解释

aligned 为有条件的实体身份对应，可列多成员；full、security 分别给出 equal/different/unknown，差异保留观察行。完整观察比较全部上下文、输入、输出和联合安全剖面；安全投影比较上下文与安全剖面，输入中安全相关的区别必须已编码在这两列内。observations 只接受完整有限关系；不完整者省略，不得用空表代替未知。preserved/modified 是完整语义有证书的子集；已对齐但观察未知时仅列 aligned。added/deleted 要求封闭覆盖、角色有据且无剩余候选。unresolved 保留版侧、局部出现及可能对应，evidence 保留两侧图摘要、节点原件见证、契约和结构索引。confidence 表示条件于契约，不是从样本估计的概率。

本实现计算 P11 必然对应的保守子集，不求解任意图同构或任意代码等价。若必须靠多步组合约束才能证明唯一，可弃判。文本改写和重构须有分析方规范角色、可信接口绑定或结构证据；没有自动释义器。没有使用 LLM、嵌入模型、匹配阈值或外部评价数据。

## 复杂度

令 n、m 为两侧分组后单元数，s 为每个单元最大槽数，q 为保留候选数。两两兼容性最坏 O(nm(1+s))，候选邻接存储 O(n+m+q)。排序未决候选至多 O(q log(max(n,m)+1))。此外须支付图规范序列化与摘要、见证读取、输入成员排序及有限表集合运算成本；共 t 行观察的输出排序最坏 O(t log(t+1))（单位长度符号）。空间还包括输入、见证、表和序列化副本。没有指数拆分搜索；因此未知分组不会被自动发现。

## 实验

Windows 项目虚拟环境执行 python -m pytest -q tests/unit/test_alignment.py：8 passed。python -m pytest -q：155 passed。ruff check .、git diff --check 通过。测试在隔离临时目录写合成快照，实际运行 extract → build_graph → build_index → align，不执行快照代码。

|事前性质|观察|
|---|---|
|程序改名并移动，受支持的指令改写|规范契约保持时得到对应且完整投影相等；新版保留不同源码路径；Accept text 与 Read text 经显式绑定对应|
|稳定身份但输出改变|完整投影不同，安全投影相同|
|稳定身份但安全剖面变化|两类投影均不同|
|同角色重复、无稳定锚点或缺少契约|保留未决；颠倒单元顺序不改变结果|
|结构绑定消歧|反序重写后按不同 operand 槽的来源交叉配对；去掉槽证据恢复歧义|
|显式聚合及反向比较|一对二、二对一可追溯；声明分组却缺少组合证书被拒绝|
|能力出现与消失|封闭作用域可确认增删；去除覆盖证书后弃判|
|观察缺失、身份约束矛盾|可确认身份但语义未知；同一稳定绑定的已知角色互斥时报告冲突|

这些结果检验的是给定可信契约时的对齐规则，不能证明从任意改写自动恢复契约或判断真实运行行为。未估算检测性能。工作止于能力对齐。
