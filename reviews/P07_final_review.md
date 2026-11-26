# P07 修复后二次独立审查

结论：**PASS**。可以申请进入 P08 的设计。本审查不修改实现，也不启动 P08。最终仍由项目负责人确认。

第一轮的 1 个 Major、3 个 Minor 和来源登记都已在当前工作区落实，并经独立复跑核对。建议项 S01 在 P07 文档中的验收口径已经满足。没有未解决的 Critical，也没有未解决的阻塞性 Major。P07 仍然是固定上游提交上的部分复现：文件模式可复核，Windows 包对入口仍然没有写出 `rogue_one_output.json`。

## 1. 二次审查范围及代码版本

| 项 | 值 |
|---|---|
| 分支 | `main` |
| HEAD | `d133e941b6bc8d606beede4280ee87ce84c84079` |
| 设计提交 | `d0f4dd9039984cc94d9e598e3d983ddd8ad1c885` |
| 与修复报告的对应关系 | 一致。修复报告登记的就是这个 HEAD，修复本身尚未提交 |
| 工作区 | P07 修复为未提交修改。另有审查开始前已存在的未跟踪日志和 P03–P06 审查报告，本次不把它们算作 P07 修复 |
| 审查方式 | 阅读两份审查材料、预检、报告、diff 和上游 `trust_domains.py`、`rogue_one_runner.py`；对照临时目录中的原始 `pair2`/`pair3`；重跑校验器、项目测试，并在新目录重跑分析器 |
| 实验解释器 | 项目 `.venv`：Python 3.14.0a5。分析器：`%TEMP%\dcfa-p07-d92d7de\venv`，Python 3.10.9 |
| 论文 PDF | 现场下载作者 PDF，SHA-256 为 `715832d5abfc613f05f2cfd64a5a5ea9bed61069b85614ec391e06b6c3635822`，与 `third_party/sources.json` 一致 |
| 上游提交 | GitHub API 返回 `d92d7de0eedb5754dc4d41b426d45a83715c0bd1`，说明为 “Add Result CSV”，提交时间 `2026-09-02T19:59:02Z`。本地源码树没有 `.git`。这是 2026 年的后续提交，登记文字也写明它与相机版的对应关系未经证实 |
| 宿主 | Windows 10.0.26300 |

`src/`、P00–P06 设计文档和上游分析器源码不在本次 diff 中。P07 没有把 RogueOne 输出接进 DCFA，也没有 P08 设计或接口。

修复触及的文件：

- 修改：`docs/P07-preflight.md`、`docs/P07-report.md`、`third_party/sources.json`、`reproduction/P07/run_pair.py`、`probe_modules.py`、`check_record.py`、`results/after.graphml`、`top-level/after.graphml`
- 新增：`reproduction/P07/portable_graph.py`、`reproduction/P07/inputs/`、`reproduction/P07/recheck/`、`tests/unit/test_p07_review.py`、`reviews/P07_review_response.md`
- 删除：无

## 2. P07 原始任务及验收标准

P07 要回答的工程问题仍是：在用户确认的上游提交上，一段无生命周期脚本的合成 JavaScript 版本对，能否让原始分析器产出图、信任域、域间流和增量结果。

预检把验收定为部分复现。原始包对命令优先运行；平台不兼容时保留可运行模块的原始返回值，并且不把模块调用计成端到端成功。本轮重新执行后，这个合同仍然成立。

P07 不重写论文 §4.2–§4.4，不建立 DCFA 对齐，不读取 P03–P06 的单快照接口。文件模式调用 `extract_idg`、`td_rel_map`、`rels_as_tuples`、`sanitize_and_export` 和 `flagged_single_local_rels_from_tuples`。包对模式调用 `process_package_pair_given_names`。

## 3. 第一轮问题逐项复核

| 问题编号 | 严重等级 | 开发 Agent 结论 | 独立验证结果 | 最终状态 | 是否阻塞 |
|---|---|---|---|---|---|
| P07-M01 | Major | FIXED | 夹具与临时目录 `pair2` 两个 `index.js` 逐字节相同；新目录重跑关系与差分均为空，过滤前规模 586/491、834/1363 | VERIFIED_FIXED | 否 |
| P07-N01 | Minor | FIXED | 发布图上的三条有向类型边和对象字段人工核对通过；反向边、改边名、改类型、改域均被拒绝；新运行的节点编号变化后检查仍通过 | VERIFIED_FIXED | 否 |
| P07-N02 | Minor | FIXED | 预检标题改为 `d0f4dd9` 运行前的历史状态，并链接最终报告 | VERIFIED_FIXED | 否 |
| P07-N03 | Minor | FIXED | 两张历史 `after.graphml` 只替换了三处与入口完全相同的绝对路径；新运行产物不再含 `Users` 或 `AppData` | VERIFIED_FIXED | 否 |
| P07-S01 | Suggestion | DEFERRED | P07 报告写明该函数先归一化再过滤，非空返回只支持候选新关系。代码没有把它写成恶意更新。P08 设计尚不存在 | VERIFIED_FIXED | 否 |
| 来源登记 | Suggestion | FIXED | 登记 1 项。PDF 摘要经重新下载核对。提交号在 GitHub 上存在，日期说明它不是 2024 相机版 | VERIFIED_FIXED | 否 |

### P07-M01

原始问题成立。修复前 `run_pair.py` 只生成顶层两行，`results/` 无法还原输入。

根本原因判断成立：负结果目录被留下，对应源码后来不在驱动里。

当前夹具：

- `inputs/function-body/1.0.0.js`：`module.exports = function (value) { return value; };`，SHA-256 `56b48c58…d36944`，54 字节，与 `%TEMP%\dcfa-p07-d92d7de\pair2\sample-1.0.0\index.js` 相同
- `inputs/function-body/1.1.0.js`：`require('path')` 之后 `module.exports = function (value) { return path.basename(value); };`，SHA-256 `0a97d18b…3b775b`，100 字节，与 `pair2` 的 1.1.0 相同
- 顶层两文件同样与 `pair3` 逐字节相同

这不是把 `path.basename('demo.txt')` 包进函数。旧版和新版都导出函数；新版把参数交给 `path.basename`。`file-mode.log` 的语句数、函数数和调用数与本轮 `function-body` 重跑一致。空关系可以按这些字节重建。

`check_record.py --case function-body` 只断言两版关系列表和差分为空。本轮另外解析了 `results/after.graphml`：导出图 229 节点、652 边，没有 `demo.txt` 或 `path.basename` 节点，同时仍有 `path`、`:local:path`、`:local:1` 等域标签。空的是 `rels_as_tuples` 的返回值，图里的内建域标签还在。报告后段把结论限制在这一输入上，这个限制是必要的。

### P07-N01

原始问题成立。旧脚本只检查见证编号是否出现在节点集合中。

当前检查从 JSON 自己的节点引用读取两条路径，要求长度分别为 2 和 3，四节点互异，返回对象相同，并核对：

- 实参 `code == demo.txt`，域为 `:local:demo.txt`
- 模块域为 `path`
- 方法名为 `path.basename`
- 返回对象类型为 `ObjTypes.APIRetVal`
- 边 `CONTRIBUTES_TO`、`PARENT_TO_CHILD`（名为 `basename`）、`FUNC_OBJ_TO_RET_VAL` 方向和类型都存在

发布图 `top-level/after.graphml` 上直接读到：

- 1713 是静态字符串 `demo.txt`，域 `:local:demo.txt`，`CONTRIBUTES_TO` 1762
- 1692 是 `ObjTypes.Require`，域 `path`，以 `basename` 连到 1741，并另有一条 `CONTRIBUTES_TO` 1762
- 1741 的名称是 `path.basename`，`FUNC_OBJ_TO_RET_VAL` 指向 1762
- 1762 是 `ObjTypes.APIRetVal`

图中还有另一个同名节点 1726。仓库里的 `recheck/top-level` 把见证方法记成 1726，发布 JSON 记成 1741。检查器跟着 JSON 走，两份记录都通过。本轮全新重跑又选中 1741，检查仍通过。编号不稳定被检查器吸收，没有退回“只看编号存在”。

独立破坏样本都拒绝，而且不限于开发测试翻转的那一条返回边：反转 `CONTRIBUTES_TO`、把边名从 `basename` 改成 `dirname`、只改 `CONTRIBUTES_TO` 的类型、只改实参信任域、把返回边改指到实参节点、给函数体记录塞入伪造关系、把顶层关系清空。缺图在仓库测试中以 `FileNotFoundError` 失败。

这些字符串是这一对合成入口的记录预言，不是面向 Skill 评价集的检测规则。

### P07-N02

原始问题成立。现在第 15 行标题是“历史预检状态（d0f4dd9，运行前）”，第 19 行指向 `P07-report.md` 的部分复现。历史段落仍保留六项未运行的原文，时点已经标明。

### P07-N03

原始问题成立。`git diff` 显示每张 `after.graphml` 有三处替换，分别在字符串节点、函数名和一条 `PARENT_TO_CHILD` 边的名称上，都从本机 `pair2` 或 `pair3` 的绝对入口改成 `sample-1.1.0/index.js`。见证节点 `demo.txt` 与 `path.basename` 不在这些行里。绝对路径字节仍留在 `d133e94`。

`portable_graph.localize_entry` 只替换与 `str(entry)` 或 `entry.as_posix()` 完全相同的 data 文本。独立探针里，大小写不同的目录、父目录、以及带前缀的字符串都保持原样。本机发布图和本轮新运行图没有残留用户目录。精确匹配是已说明的发布规则，当前产物满足“图中不再出现本机用户目录”。

### P07-S01 与来源登记

`flagged_single_local_rels_from_tuples` 先把 `:local:*` 归一成 `:local`，再做集合差，并用 `apply_rel_filters` 去掉纯本地域关系。上游实现见固定树 `fast/dataflow/trust_domains.py` 第 274–278 行和第 411–417 行。论文 §4.4 比较的是跨域流集合，并在旧版良性的假设下把非空新集合标成 rogue update。P07 保存的是这个函数的返回值。

报告第 9 行和第 49 行写明非空输出不能证明恶意意图或动态执行。`reproduction/P07` 的驱动和测试没有恶意标签。P08 设计文件不存在，因此“写进 P08 设计”只能作为进入 P08 时的约束，不能算 P07 的未完成实现。

登记项 `rogueone-p07` 的 `kind` 为 `original`，`pin_basis` 写明相机版对应关系未经证实。这个措辞与 2026-09-02 的提交日期相符。`dcfa check-sources` 接受该清单，返回 count 1。

## 4. 开发 Agent 修复方案评价

方案没有改上游算法，也没有改阶段一实现。函数体输入按字节恢复，顶层与函数体共用 `run_pair.py` 的目录构造，校验器按 `--case` 使用不同预言，发布图只改写入口路径。这些都对着第一轮的证据缺口，而不是对着某个外部样本编号。

修复前行为有代码和临时文件可以核对，不是只凭修复报告回顾。旧校验器的漏洞由本轮破坏样本重新证实已经闭上。包对失败没有被改成成功。

有一处表述仍可被读宽。报告第 22 行仍说“初次函数体形式的样例没有得到域间关系”。恢复出的程序是导出函数加上参数调用。本轮把同一常量调用放进被调用的函数后，差分重新变成非空。第 47 行已经把空关系限制在该输入上。这是文档精度，不是算法回退。见第 12 节的建议。

## 5. 核心算法重新验证

P07 没有新增数学定义。本轮核对的是被调用的上游切片是否仍按原函数行为留下证据。

| 性质 | 本轮观察 |
|---|---|
| 直接数据流 | 顶层 `path.basename('demo.txt')` 给出 `(:local:demo, path)`，归一化差分为 `(:local, path)`。三条类型边连接实参、模块、方法和同一个返回对象 |
| 共现不构成流 | `require('path')` 与 `module.exports = 'demo.txt'` 同时存在时，两域都出现，关系列表为空 |
| 既有流不重复计为新增 | 两个版本都是顶层 `basename` 时，两边关系相同，差分为空 |
| 删除不记成新增 | 旧版有 `basename`、新版只导出常量时，旧关系存在，新关系为空，差分为空 |
| 同一模块的另一方法 | `path.dirname('demo.txt')` 的归一化差分仍是 `(:local, path)`。方法名留在图节点 `path.dirname` 上，不留在归一化二元组里 |
| 引号与中间变量 | 双引号字面量，以及 `const name = 'demo.txt'` 再经三元表达式调用，仍得到同一归一化差分 |
| 别名调用 | `const b = path.basename; module.exports = b('demo.txt')` 的关系列表为空。直接成员调用的正结果不能外推到这种写法 |
| 被调用的函数体 | `function f(){ return path.basename('demo.txt'); } module.exports = f();` 得到与顶层相同的归一化差分 |
| 嵌套调用 | `f(f('demo.txt'))` 产生两条具体路径，归一化后仍是一个 `(:local, path)` |
| 入口文件计数 | `file_node_nums` 在成功分析中仍是 `{}`。该字段只在 `get_module_exports` 处理被 require 的文件时写入。这两个合成包的入口文件不走那条路径，所以包对警告会在分析成功后出现 |
| 原生结果 | `mem_info` 读取 Windows `pmem.shared` 时抛出 `AttributeError`。异常发生在结果字典构造期间，`rogue_one_output.json` 写在 `try` 之外，因此文件没有生成 |

`file_node_nums` 为空不能解释成“文件没有被解析”。文件模式在该字段为空时仍给出 AST、域和见证边。包对入口的失败点是遥测字段，警告是另一条上游计数路径。两件事都保留为未完成的端到端复现，没有被合并成一次检测成功。

底层 stdout 里的 `Detection: failed` 仍是分析器自己的漏洞扫描字段。域差分记在 JSON 返回值中。

## 6. 语义及关系建模复核

本次没有新的 DCFA 图，也没有跨版本对象对齐。旧版顶层导出图在 `sanitize_and_export` 之后为 0 节点、0 边；过滤前 JSON 仍是 572 节点、477 边。新版导出图为 233 节点、667 边。

关系方向与 §4.2 的外部调用一致：实参和被调函数对象都指向返回值。模块对象到返回值还有一条额外的 `CONTRIBUTES_TO`。检查器要求三条见证边，不靠添加边来提高连通性。

函数体负例的导出图没有 `basename` 节点。它的 `path` 域来自模型里的模块对象，没有对应的跨域元组。顶层正例才能把 `:local:demo.txt` 和 `path` 连成元组。

节点编号在同一次审查的不同运行之间会在 1741 与 1726 之间更换，两个节点的名称都是 `path.basename`。语义检查不把编号当成身份。

## 7. 证据完整性复核

顶层和函数体源码都在 `reproduction/P07/inputs/`，并与产生历史结果的临时 `index.js` 逐字节相同。行尾是 CRLF。`inputs/.gitattributes` 将 `*.js` 标成 `eol=crlf`，检出后的工作区字节可以维持当前摘要。

发布图把入口绝对路径换成包内相对路径。原始绝对路径留在 HEAD `d133e94`。关系 JSON 使用节点编号，不依赖那条路径。

`recheck/` 保存了修复时的新运行。本审查没有把该目录当作唯一证据，而是在 `%TEMP%\p07-review2-exp` 再次生成输入、调用当前 `probe_modules.py`，再调用 `check_record.py`。

历史 `npm-install.log` 只含安装警告，不含命令行。报告已写明 `--ignore-scripts` 不能由该日志单独证明。本轮没有重新安装依赖，也没有执行合成 `index.js` 的 Node 程序。

解析失败和缺文件没有写成空关系：

- 新版源码缺少括号时，进程退出码 1，上游在 `opgen.py` 中以 `ZeroDivisionError` 终止，输出目录没有 `module-returns.json`
- 缺少 `index.js` 时，进程退出码 1，没有结果 JSON

失败形态是未捕获的上游异常，不是一套分类后的错误码。对当前驱动，失败没有被记成空的良性差分。

## 8. 原始反例复测

命令使用 Python 3.10.9。输出在临时目录，不写回仓库。

| 编号 | 输入 | 理论预期 | 实际 | 结论 |
|---|---|---|---|---|
| R1 | 归档顶层字节，新的包对目录 | 过滤前 572/477 与 836/1377；关系 `(:local:demo, path)`；差分 `(:local, path)`；检查通过；图中无用户目录 | 规模、关系和差分相同；见证方法为 1741；`check_record.py` 退出 0；无绝对路径 | 通过 |
| R2 | 归档函数体字节 | 两版关系和差分为空；过滤前 586/491、834/1363 | 与预期相同；导出图无 `basename`；`check_record.py` 退出 0 | 通过 |
| R3 | 两个 case 的 `run_pair.py` | 退出码非 0，且不产生 `rogue_one_output.json` | 两者均为 `AttributeError: 'pmem' object has no attribute 'shared'`，退出码 1，原生 JSON 不存在 | 通过 |

包对日志仍打印 `No files processed`。结合第 5 节，该警告与“入口文件没有进入 `file_node_nums`”一致，不能单独作为文件未被解析的证据。

## 9. 第二轮独立反例

预期先按上游函数的集合差和 §4.2 的调用边写下，再执行。旧版除特别说明外都是 `module.exports = 'demo.txt'`。分析器时间约 0.17–0.21 秒。

| 编号 | 新版输入的要点 | 预期 | 实际 | 结论 |
|---|---|---|---|---|
| V1 | 只 `require('path')` 并导出 `demo.txt`，不调用方法 | 两域可以同时出现，关系必须为空 | 域含 `:local:demo.txt` 和 `path`；关系与差分均为空；导出图有 `demo.txt` 节点，没有 `basename` 节点 | 通过。正结果不是共现造成的 |
| V2 | 函数返回 `path.basename('demo.txt')`，再 `module.exports = f()` | 若调用被解析，应出现与顶层相同的归一化差分 | 关系 `(:local:demo, path)`，差分为 `(:local, path)` | 通过。空关系不能概括所有函数体 |
| V3 | 两个版本都是顶层 `basename` | 差分必须为空 | 两边关系相同，差分为空 | 通过 |
| V4 | 旧版 `basename`，新版只导出常量 | 删除流不进入新集合减旧集合的结果 | 旧关系存在，新关系为空，差分为空 | 通过 |
| V5 | `path.dirname('demo.txt')` | 模块域关系仍可出现，方法名应留在节点上 | 归一化差分仍是 `(:local, path)`；节点名为 `path.dirname` | 通过。二元组不区分方法 |
| V6 | 双引号 `path.basename("demo.txt")` | 与单引号同一关系名 | 关系与差分和顶层相同 | 通过 |
| V7 | `const name = 'demo.txt'`，再经三元表达式调用 `basename(name)` | 字面量经变量仍可形成同一关系 | 关系与差分和顶层相同，节点编号不同 | 通过 |
| V8 | `const b = path.basename; b('demo.txt')` | 不预设一定等于直接调用 | 域中有 `demo.txt` 和 `path`，关系与差分均为空 | 记录为上游切片的边界，不是本次修复的回归 |
| V9 | `f(f('demo.txt'))` | 嵌套调用若被解析，具体路径可以多于一条，归一化对可以合并 | 两条具体路径，归一化差分一个 `(:local, path)` | 通过 |
| V10 | 新版缺少右括号 | 非零退出，且不写空的成功记录 | 退出码 1，无 `module-returns.json` | 通过 |
| V11 | 包目录没有 `index.js` | 非零退出，且不写空的成功记录 | 退出码 1，无结果 JSON | 通过 |
| V12 | 发布图的独立破坏，见第 3 节 N01 | 缺边、反转、改名、改域均失败 | 全部以 `ValueError` 或 `FileNotFoundError` 失败 | 通过 |

V2 说明第 22 行的“函数体形式”比恢复出的程序更宽。V5 说明只保存归一化二元组时，`basename` 与 `dirname` 落入同一对。V8 说明成员调用的正结果有句法边界。三件都是这个上游切片的适用范围，P07 驱动没有把它们伪装成更强的检测器。

## 10. 前置依赖与端到端验证

P07 驱动不导入 `dcfa`。本次 diff 没有修改 `src/` 和 P00–P06 设计文档。全套单元测试 104 项通过，其中 P07 新增 13 项；其余原有测试没有失败。

适用的端到端是合成包对到文件模式，再到校验器。R1 与 R2 在新目录走完这条链。P03 的 SCS、P04 的能力图和 P05/P06 的证据索引不在这条链上，本轮没有把它们串成一次假的跨阶段实验。

`third_party/sources.json` 只增加登记数据。`tests/unit/test_cli.py` 在临时目录使用空清单夹具，不会改写仓库清单。登记校验的 schema、字段和 `kind` 仍由原 `dcfa.registry` 执行。

没有发现用 P07 临时逻辑掩盖 P00–P06 缺陷的路径。前置阶段不需要因这次修复重开验收。

## 11. 完整回归测试结果

| 命令 | 环境 | 退出码 | 结果 |
|---|---|---|---|
| `.venv\Scripts\python.exe -m pytest -q --tb=line` | Python 3.14.0a5 | 0 | 104 通过，0 失败，0 跳过，2.28 秒 |
| `.venv\Scripts\python.exe -m pytest tests/unit/test_p07_review.py -q --tb=no` | 同上 | 0 | 13 通过，0.91 秒 |
| `.venv\Scripts\ruff.exe check .` | Ruff 0.17.6 | 0 | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | Ruff 0.17.6 | 0 | 59 files already formatted |
| `git diff --check` | Git | 0 | 仅有 CRLF 转换提示，无空白错误 |
| `.venv\Scripts\python.exe -m dcfa check-sources` | Python 3.14.0a5 | 0 | status ok，count 1 |
| 第 8–9 节的分析器重跑 | Python 3.10.9 | 0（驱动脚本） | 各案退出码见上表；包对两案为 1；语法错误和缺文件为 1 |
| 类型检查 | 无 mypy/pyright 配置 | NOT_RUN | 未执行 |
| 大规模性能 | — | NOT_RUN | 未执行。单次文件分析约 0.17–0.21 秒，与第一轮“1 秒以内”同量级 |
| P00–P06 单独 `--ignore` 命令 | — | NOT_RUN | 未单独重跑。全套 104 项包含这 91 项且没有失败项 |
| P03 至 P07 的跨阶段串联 | — | NOT_RUN | 不适用。P07 不消费这些接口 |

第一轮 T01、T03、T17、T18、T21–T25、T28 所对应的文件模式、包对失败、见证边、旧版空关系、无害样本的非空函数返回，均在 R1–R3 和发布图人工核对中复现。T13 的函数体负例现在可以按入库字节重建，对应 R2。

## 12. 新发现的问题

### P07-R2-S01　“函数体形式”一句仍宽于恢复出的程序

- 严重等级：Suggestion
- 证据状态：CONFIRMED
- 文件：`docs/P07-report.md` 第 22 行；同文第 47 行已经收窄
- 描述：第 22 行把 `results/` 概括为函数体形式没有域间关系。恢复的 1.1.0 是导出函数，并让参数进入 `path.basename`。V2 把常量调用放进被调用函数后，归一化差分为 `(:local, path)`。
- 根本原因：早期句子按句法外形概括，后来的字节恢复揭示这个负例还改变了导出值和实参。
- 影响：只读第 22 行会把空关系理解成函数体语法的一般性质。同页后段和夹具能纠正这个读法。检测结论没有被抬高。
- 修复建议：让第 22 行指向 `inputs/function-body/` 的两个文件，并写明空的是该输入的关系元组。
- 验收：报告不再把这一空关系表述成任意函数体都没有跨域元组。
- 是否阻塞 P08：否

没有新的 Critical、Major 或 Minor。路径替换的大小写探针、归一化二元组不区分 `basename` 与 `dirname`、以及别名调用没有形成元组，都记录在第 9 节和第 14 节。它们是精确替换规则和上游切片的适用范围，当前发布产物和文档限制与这些观察一致。

diff 中没有看到评价集分支、样本编号特判、阶段一行为变化或 P08 实现。`check_record.py` 中的 `demo.txt` 与 `path.basename` 只约束这份已经公开的合成记录。

## 13. 第一轮与第二轮评分对比

| 评价维度 | 第一轮评分 | 第二轮评分 | 变化 | 变化依据 |
|---|---:|---:|---:|---|
| 原始任务完成度 | 13 | 14 | +1 | 函数体输入可按原字节重建，空关系已重跑。原生包对结果和完整集合差仍未取得，所以不到 15 |
| 算法正确性 | 20 | 20 | 0 | 驱动仍调用同一个上游切片。共现、删除和重复版本的独立结果与该切片一致，别名调用和归一化丢方法名也是该切片原有边界 |
| 科研严谨性 | 17 | 18 | +1 | 负对照可重建；来源清单写明相机版未证实，PDF 摘要和 2026-09-02 的提交日期已独立核对。端到端仍是部分复现 |
| 软件架构与代码质量 | 8 | 9 | +1 | 路径改写与记录检查分开；包对异常仍向外传播。脚本仍依赖本机上游树 |
| 测试有效性 | 11 | 14 | +3 | 仓库测试覆盖边、字节、破坏样本和登记。共现、别名、解析失败只在本轮审查执行，没有进入仓库，所以不到 15 |
| 鲁棒性与安全性 | 4 | 4 | 0 | 语法错误和缺文件以非零退出结束，没有空成功记录。安装日志仍不能单独证明 `--ignore-scripts` |
| 可复现性 | 3 | 4 | +1 | 夹具与 `pair2`/`pair3` 逐字节相同，新目录重跑通过。仓库仍不含上游源码，节点编号跨运行不稳定 |
| 阶段隔离与接口设计 | 5 | 5 | 0 | 未改阶段一，未把 RogueOne 接入 DCFA，未实现 P08 |
| 总分 | 81 | 88 | +7 | 证据和测试补上了第一轮扣分点。部分复现没有被改记成端到端成功 |

## 14. 当前剩余风险

- Windows 上的包对入口仍在写出原生 JSON 之前失败。P08 不能把文件模式返回值当成 `rogue_one_output.json`。
- `(:local, path)` 是归一化后的候选新关系。`dirname` 与 `basename` 会得到同一个二元组。它不是恶意更新结论，也不是方法级身份。
- 别名调用 `b = path.basename; b('demo.txt')` 在这次探针中没有形成关系。直接调用的正结果不能外推到语义等价的全部写法。
- 函数体空关系只属于已恢复的那两个文件。被调用且导出返回值的常量调用会产生非空差分。
- 上游提交是 2026-09-02 的 “Add Result CSV”，不是已证明的 ICSE 2024 相机版。
- 节点编号会在两次运行中改变。后续比较应使用对象字段和边类型。
- `npm --ignore-scripts` 仍只有命令记录，没有由安装日志独立证明。
- 发布图的入口路径是改写后的相对路径。未改写字节在 `d133e94`。

这些限制都不改变“部分复现”这一已验收的阶段合同。

## 15. 最终验收结论

**PASS**。

对照本阶段合同：

- 文件模式和包对失败都按设计留下证据，函数体输入已经可重建
- 记录的返回值与上游 `flagged_single_local_rels_from_tuples` 的归一化和集合差一致，报告没有把它写成 §4.4 的完整恶意判定
- 无未解决 Critical，无未解决阻塞性 Major
- 第一轮问题均已独立复验
- 原始顶层正例、函数体负例，以及共现、重复、删除、引号、变量、被调用函数和嵌套调用均按事先写下的预期出现
- 见证边、域和返回对象类型能在图上读到
- 解析失败和缺文件没有变成空关系
- 阶段一测试随全套通过，阶段一源码未改
- 合成包到文件模式再到校验器的链路在新目录通过
- 没有评价集标签或样本特判
- 研究边界仍是同一个合成版本对上的原始程序运行
- 文档中的部分复现、非恶意推断和入口路径改写与代码一致
- 未取得的原生包对结果仍写为未取得

允许留下的非阻塞项是 P07-R2-S01，以及第 14 节的已知边界。

## 16. 是否具备进入 P08 的条件

具备申请条件。项目负责人确认前不进入 P08。

P08 可以使用的材料只包括：

- 顶层合成版本对的文件模式图、域、`(:local:demo, path)`、归一化差分 `(:local, path)`，以及实参、`path` 模块、`path.basename` 和共同返回对象之间的三条有向边
- 已恢复函数体输入的关系列表为空；该结论不推广到其他函数写法
- 当前 Windows 环境下包对入口没有完成，没有 `rogue_one_output.json`
- `(:local, path)` 不是恶意更新证明，也不区分同一模块上的不同方法
- 上游提交是用户确认的 `d92d7de`，PDF 摘要已核对，它不是已证明的论文相机版

P08 的设计若使用这次差分，必须保留上述限制。不需要为 P07-R2-S01 再开一轮实现修复才能开始 P08 设计；若修订报告，只改第 22 行的概括范围。
