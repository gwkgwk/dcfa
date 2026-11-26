# P03 独立审查报告

结论：**CONDITIONAL PASS**。当前不得进入下一阶段。读取边界、证据骨架和阶段隔离可以保留；在标题漏提取、缩进误提取、无效声明的置信度、端口 `null` 语义、条目上限误诊、Windows 备用数据流，以及默认可安装性修复并回归之前，不能把这份 SCS 当作内部能力流的输入。

本次没有 Critical。存在未修复的 Major，因此也不能给出 PASS。总分 60，不能抵消这些缺陷。

## 1. 审查范围与环境

| 项 | 值 |
|---|---|
| 分支 | `main` |
| HEAD | `5157a4bf8a7d1f204f6e4d51eb303ee7095b34dc` |
| 设计提交 | `e220fcc9c7c26bd86be84d07e4a633f759706cd6`（只含 `docs/P03-design.md`） |
| 实现提交 | `5157a4b`（报告、示例、提取器、测试与夹具） |
| 审查开始时工作区 | 干净 |
| 平台 | Windows，Python 3.14.0a5（MSC v.1942 64-bit） |
| 通过测试时的依赖 | 纯 Python PyYAML 6.0.4（`yaml.__with_libyaml__ is False`）、fastjsonschema 2.22.3、pytest 9.2.0、ruff 0.17.6 |

审查阅读了 `README.md`、`AGENTS.md`、`docs/templates/stage.md`、`docs/P00-design.md`、`docs/P03-design.md`、`docs/P03-report.md`、`docs/reproduction/knotscryer_scope.md`、`docs/reproduction/knotscryer_analysis.md`、`docs/reproduction/knotscryer_code_mapping.md`、`references/source_manifest.json`，以及 `src/dcfa/skill_reader.py`、`src/dcfa/scs.py`、`src/dcfa/scs.schema.json`、`src/dcfa/cli.py`、对应单元测试、合成夹具和 `examples/p03-scs.json`。

论文对照使用本次获取的 arXiv HTML：`https://arxiv.org/html/2610.32155v1` 的 §III-B/C。仓库声明官方实现未定位；本地没有可逐行对照的上游源码。

审查限制：

- 仓库中没有独立的 P03 任务书。验收对照的是 `AGENTS.md` 的方法顺序第 1 步、阶段模板、P01 划定的单 Skill 边界、`docs/P03-design.md` 和报告自述。下面不把审查委托书里的想象要求写成原始需求。
- 没有 P02 的设计或实现。阶段号从 P01 跳到 P03。这不单独构成功能缺陷，但无法核对是否存在一份未入库的 P02 任务书。
- 报告中的 Python 3.10.9 结果、以及“wheel 内含 schema”的打包结果，本环境没有复核。临时环境缺少 setuptools，`--no-build-isolation` 的 wheel 构建停在 `Cannot import setuptools.build_meta`。运行中的可编辑安装能够读到 schema，否则 `extract` 会在校验前失败。
- 文件符号链接创建失败（WinError 1314，客户端缺少特权）。目录 junction 和硬链接已测。不能把未执行的符号链接写成已验证。
- 未读取仓库外评价集，未执行待分析 Skill 中的脚本。探针只调用 `extract` / `scan`。

审查没有修改 `src/`、`tests/`、`examples/` 或夹具。

## 2. P03 实际实现内容

P03 实现的是单个静态目录的证据型能力摘要，不是能力流图，也不是版本差分。

`skill_reader.scan` 拒绝 `..`、UNC、父目录和根上的重解析点、符号链接、硬链接和非常规文件；预算为 256 项、相对路径分量少于 12 的目录才继续下降、单文件 32 KiB、已解析内容合计 256 KiB。只把根文档、`.py` 和根级或非资源目录中的 YAML 读成文本。其余文件登记角色后标 `inventory_only`。

`scs.extract` 产出 schema `p03.1`。主张分五组：端口、效果、操作、上下文暴露、信任边界；证据内联在每条主张上。来源有三条：

- YAML frontmatter 或独立 `.yml`：标量或单层字符串映射；
- 整行完全匹配的两条英文句式；
- Python `ast.walk` 见到的、目标可写成名称链的调用表达式。

`status` 只有在存在 `SKILL.md` 且诊断数组为空时才是 `complete`。任一空分组都会追加 `no_claim_*`。CLI `dcfa scs DIRECTORY` 在 `complete` 时返回 0，否则返回 1；参数错误由 argparse 返回 2。

实现里没有跨 Skill 边、策略自动机、LLM、提示词或版本对齐。

## 3. 原始任务要求逐项验收表

对照材料是 P03 设计第 1–11 行、P01 对 §III-B 的边界，以及 `AGENTS.md` 的第 1 步。没有另行编造任务条目。

| 要求 | 判定 | 依据 |
|---|---|---|
| 先提交设计，再写实现 | 部分实现 | `e220fcc` 确实早于实现，但设计只有 11 行，没有句式、状态机、置信度或失败语义的可证伪定义。规则第一次出现在实现提交里 |
| 只读、有界、拒绝链接和硬链接 | 已完整实现 | 代码与探针一致。junction 和硬链接没有把外部标记字符串带入 JSON。文件符号链接未实证 |
| 三种论文提取途径都有对应代码 | 部分实现 | YAML、整行英文和 Python 调用都存在。英文只覆盖两条正则；脚本只记录调用，不记录技能暴露的动作。论文所说“规则难以捕获的语义属性”按 P01 明确不做，不记为漏项 |
| 六类信息、缺证用 `null`、失败用诊断 | 实现错误 | 数据结构在。`null` 和“未识别行为必须有诊断”这两条契约被第 9 节的 P03-1、P03-4 打破 |
| 证据含路径、片段、方法、分值，并可对回源行 | 已完整实现 | 合成样例和探针中的片段与行号能够对回文件。分值是未校准的 1.0/0.5，报告已说明 |
| 不调用模型，不做跨 Skill | 已完整实现 | `src/dcfa` 中没有模型客户端、handoff 或第二份 Skill 的图算法 |
| Schema 拒绝非法结构，CLI 退出码符合设计 | 已完整实现 | 手工删字段会触发校验异常。缺少参数和多余参数返回 2；失败目录返回 1 且 stdout 是 JSON；完整传输句返回 0 |
| 合成夹具可重建已保存的 SCS | 已完整实现 | 本次 `extract(scs-demo)` 与 `examples/p03-scs.json` 逐字段相等。单元测试本身没有引用该文件 |
| 测试不把工程通过解释成召回率 | 已完整实现 | 设计和报告都写了这条限制，测试也没有报告准确率 |
| 复现 KnotScryer 的单 Skill SCS 提取 | 部分实现 | 复现的是字段骨架和三类来源的名字。提取规则是项目自定的窄子集，而且子集的判定还有误报和漏报 |
| 内部能力流、RogueOne 差分、DCFA 对齐 | 未实现 | 按 P03 自己的设计，这些不属于本阶段。不能据此说 P03 越界，也不能把它们算作 P03 已完成 |

报告第 27–41 行对预算、`complete` 的含义、不衡量召回率和不证明恶意意图的陈述，与代码的主路径一致。报告没有披露标题、缩进、备用数据流和条目上限误诊。

## 4. 算法正确性分析

读取器和“语法上存在的调用”这部分是确定的，重复调用 `extract` 得到同一字典。调用顺序是 `ast.walk` 的广度优先，不是源码顺序：函数内外都有 `a()`、函数内还有 `b()` 时，Python 操作名顺序是外层 `a`、内层 `a`、内层 `b`。这与当前设计不冲突，因为设计没有承诺源码顺序。

正确的保守行为也包括：YAML 锚点、别名和显式标签在组合对象之前被拒绝；`!!python/object/apply` 不会执行，整份声明失败；多文档 YAML 给出 `invalid_yaml`，不会静默留下第一份文档；超长证据片段被丢弃并带诊断；500 个 token 之后的调用不会被解析，同时有 `python_token_limit`；目录 junction 和文件硬链接不会把外部字节带入摘要。

下面几处则是判定错误，不是覆盖不足。

标题被当成空白行。`document` 在匹配句式之前执行 `stripped.startswith("#")` 后直接 `continue`，不调用 `issue`。因此下面的文件没有诊断，`status` 为 `complete`，唯一端口类型是 `Text`。标题中的 `Command` 传输不会出现在任何主张或诊断里：

```text
# Send command from workspace to external.
Send text from local to external.
```

设计要求未识别行为进入 `diagnostics`。这行文本本身符合实现自己的传输文法，却没有任何记录。`complete` 在这里表示“主张集合已经封闭”，而集合是错的。

缩进代码被当成真实能力。匹配前使用 `line.strip()`，四格缩进被去掉。下面这一行单独构成的文件得到 `status == complete`、空诊断、输出端口 `Command`、效果 `send` 且 `crosses_boundary == True`、信任边界 `workspace -> external`，置信度 0.5。证据片段仍保留前导空格，所以人工还能看见缩进；结构化字段已经把它当成一次跨信任域发送。

```text
    Send command from workspace to external.
```

`null` 的定义没有被实现遵守。设计写明缺少可靠属性时用 `null`。传输正则已经捕获 `origin`，并把它写入 `trust_boundaries.source`，但端口只写了 `exposure_scope`。`Send text from local to external after explicit authorization.` 的端口 `trust_origin` 仍是 `null`。单元测试把这个结果写成了断言。

无效 YAML 形状仍得到直接声明级置信度。`input: [Text]` 不是标量也不是映射，实现仍追加一个 `data_type is None` 的端口，`evidence.confidence` 为 1.0，然后再追加 `incomplete_port_declaration`。1.0 在报告中的定义是“直接语法或声明”。这里并没有一份可用声明。

条目上限会把“文档还在”说成“文档不存在”。根目录有 `SKILL.md` 再加 256 个其他文件时，扫描在处理任何文件内容之前返回。结果是 `status == failed`、端口数为 0，诊断同时包含 `entry_limit` 和 `required_document_unavailable`。后者与已通过的预检查不符。

Windows 备用数据流不在分析范围内，也不会留下诊断。主数据流只有一条合法传输句、隐藏流中另有一条 `Command` 传输时，结果是 `complete`、没有 `Command` 端口，JSON 中也不出现流名称。同一读取器已经专门处理重解析点和硬链接，备用数据流是这条边界上的空洞。

`operations` 的算法对象与论文用词不同，见第 5 节。就实现自己的“调用表达式”定义而言，可命名调用、动态目标和默认参数中的调用都按代码执行，没有发现与该窄定义相反的崩溃。

## 5. 论文方法与实现一致性分析

官方源码不存在，不能做函数级对照。对照文本是 v1 §III-B 的这一段：SCS 结合 YAML frontmatter、自然语言启发式和脚本静态扫描；端口记录类型、敏感性、信任来源、暴露范围和可消费性；效果带敏感性保持、跨边界和授权；操作记录技能暴露的主要动作及参数；证据记录文件、片段、方法和置信分值。

| 论文内容 | 实现 | 归类 |
|---|---|---|
| 一个 Skill 一份 SCS，六类信息 | 五组数组加内联证据 | 忠实于论文概念。输入和输出合成端口组，与 P01 的读法一致 |
| YAML frontmatter | `BaseLoader` 组合节点，拒绝别名、锚点和标签，只接受单层字符串 | 合理适配。论文没有键名；本地键集合是项目约定，报告写了 |
| 自然语言启发式 | 两条必须整行匹配的英文句式 | 未经论证的窄化。论文没有文法，项目必须自定规则；当前规则不是一般启发式，而且标题和缩进会改写结果 |
| 规则难以捕获的语义属性 | 明确不做，无模型和提示词 | 与 P01 一致的边界，不是偷偷删掉的步骤 |
| 脚本静态扫描 | 仅 Python，且只记录可命名调用 | 合理的语言子集，但字段语义有未经论证的替换 |
| 操作是技能暴露给 Agent 的动作 | `render(value)` 不会成为操作，`value.strip()` 会 | 未经论证的修改。合成样例的操作名是 `accept`、`return`、`value.strip`，没有 `render` |
| 证据与置信度 | 路径、行号、片段、方法、1.0 或 0.5 | 行号和两个固定分值是项目新增。未校准这一点报告写了；1.0 用在无效声明上与报告定义不符 |
| §III-C 内部边和跨 Skill handoff | 没有图 | 符合 P03 设计。不是本阶段的忠实复现项 |
| 策略搜索与两层验证 | 没有 | 符合项目范围 |

因此可以称它为“带证据的 SCS 数据契约的重实现”，不能称它为“KnotScryer 提取算法已经复现”。P01 已经说明论文没有给出可执行规则；P03 的问题不是缺少官方源码，而是自定规则尚未达到设计里那条诊断契约，并且借用了论文的 `operations` 名称。

## 6. 科研科学性评价

有做到的部分：提取器没有按 `synthetic-summary`、`format.py` 或某条攻击字符串分支；夹具句子只是落在公开正则里。报告把置信度、召回率和恶意意图分开。空分组变成诊断，而不是变成良性。分析失败不会被写成 `complete`，除了第 4 节那些诊断根本没被发出的情况。外部评价集没有参与规则设计，仓库里也没有挂载它。

没有做到的部分：

- 实现前的设计不能证伪后来的正则、置信度和状态机。验收模板要求的形式化定义、可证伪条件和异常契约是在代码之后才由报告描述的。
- `tests/unit/test_scs.py` 的 `test_transfer_instruction` 断言 `trust_origin is None`。测试把与设计冲突的映射固定成了正确结果，再用通过来证明实现正确。
- `test_cli` 用同一次 `extract()` 的返回值对比 CLI。这只证明两个入口相连，不证明摘要内容正确。
- `complete` 可以被后续实验误当成“能力集合已完整”。标题夹具说明这个读法不成立。报告虽然写了 `complete` 只表示规则跑完，但规则本身会跳过符合文法的标题。
- 若下一阶段把 `python_ast` 操作直接送入“Agent 能否为该动作提供参数”的论文判据，合成样例会把 `str.strip` 当成技能动作，把真正的 `render` 漏掉。这会污染后续基线。

测试通过没有证明提取正确。提取在若干构造句上符合正则，也没有证明“单 Skill 能力摘要已经可以支持安全结论”。P03 还没有、也不应该声称后一件事。

## 7. 软件工程质量评价

模块边界清楚：`skill_reader` 只做目录和字节，`scs` 做解释和校验，`cli` 做退出码。Schema 随包发布，非法结构不能被静默写出。诊断带路径和行号。文件名在目录内排序，输出在同一解释器上可重复。没有发现 Skill 名称特殊分支，也没有发现执行、安装依赖或访问 Skill 内 URL 的代码。

主要工程问题是结果契约过粗。`read_failure`、空类别、未解释正文和 `inventory_only` 都折叠成 `partial`，CLI 一律返回 1。文档缺失才是 `failed`。下一阶段不能把退出码 1 当作风险标签。

角色优先级也比后缀粗。`scripts/` 或 `templates/` 下的 YAML 不会按元数据解析；根上的 `.json` 和 `.toml` 角色是 `metadata`，实际却是 `inventory_only`。这些情况有诊断，所以不是静默成功，但 `files[].role` 会让调用方以为 JSON 已被当作元数据读取。

`validate()` 每次重新编译 schema。CLI 没有接住提取过程中的异常；本次探针没有构造出能使合法输入抛异常的样子，这是残余风险，不是已复现故障。

## 8. 独立测试设计及实际结果

预期先按源码和设计写出，再在临时目录调用当前 `extract`。下表只列能决定审查结论的样本。

| 样本 | 审查前预期 | 实际结果 |
|---|---|---|
| 空目录 | `failed`，文档不可用 | `failed`。除预期诊断外，还有五条 `no_claim_*` |
| 一条授权传输句 | `complete`；若遵守 `null` 契约，`trust_origin` 应为 `local` | `complete`，边界来源是 `local`，端口 `trust_origin` 为 `null` |
| 标题中的另一条传输句加正文传输句 | 标题应提取，或至少有诊断，不能在丢掉 `Command` 后仍为 `complete` | `complete`，诊断为空，只有 `Text` |
| 四格缩进的传输句 | 应视为未解释示例，不能是 `complete` | `complete`，诊断为空，生成 `Command` 和 `crosses_boundary: true` |
| 闭合围栏内一条、围栏后一条 | 围栏内不提取，但有诊断 | `partial`，只有围栏后的 `Text`，诊断为 `embedded_example` |
| 未闭合围栏直到文件末尾 | 后续句子被吞 | `partial`，端口为空；只有开头的 `embedded_example` 和 `no_claim_*`，没有逐行诊断 |
| `input: [Text]` | 不应产生置信度 1.0 的端口 | 一个 `data_type: null` 的端口，置信度 1.0，另有 `incomplete_port_declaration` |
| 信任边界多一个 `revoked` 键 | 应有未知属性诊断 | 结构化字段没有该键，片段里仍有原文，没有对应诊断。`partial` 只来自缺少操作 |
| 第二个 YAML 文档 | 审查最初误以为会静默保留第一文档 | 实际是 `invalid_yaml`，第一文档也不保留。这是保守失败，不列为缺陷 |
| `def render` 只调用 `value.strip()` | 按论文应出现 `render`；按当前代码只会出现 `value.strip` | 只有 `value.strip` |
| 会写标记文件的 Python，以及 YAML 应用标签 | 标记文件不出现，标签不执行 | 均成立 |
| 注释把 token 数推过 500，其后调用 `danger()` | `danger` 不出现，并有 token 诊断 | 成立 |
| `skill.md` 大小写 | 审查最初预期 Windows 上会失败 | `Path("skill.md") == Path("SKILL.md")` 为真，文件被当成文档并 `complete`。不构成 Windows 缺陷。POSIX 大小写敏感行为未测 |
| 主数据流合法、ADS 中另有传输句 | 不应是无诊断的 `complete` | `complete`，ADS 内容不可见 |
| 硬链接和目录 junction 指向外部秘密 | 秘密字符串不出现 | 成立。文件符号链接未能创建 |
| 11 层目录中的调用、12 层目录中的调用 | 前者可读，后者有 `depth_limit` | 成立，与 `len(path.parts) < 12` 一致 |
| 257 个目录项且含 `SKILL.md` | 应说明超限，不应声称必需文档不存在 | 端口为 0，`failed`，两种原因同时存在 |
| 4 字节等于临时上限、5 字节超过上限 | 等于上限可读，超过则 `byte_limit` | 成立 |
| 连续两次提取、以及样例 JSON | 相同 | 都成立 |
| CLI 参数数量、失败目录、完整目录 | 退出码 2、1、0，stdout 是 JSON | 成立 |
| `nul.py` | 检查 Windows 保留名是否卡死或被当成设备 | 创建的是普通文件，`danger()` 被正常提取。不构成缺陷 |

开发者测试在纯 Python PyYAML 下为 `30 passed in 0.83s`。`ruff check .` 和 `ruff format --check .` 通过。

默认安装不通过。新建虚拟环境执行 `pip install -e '.[dev]'` 时，PyYAML 解析为 `pyyaml-6.0.4-cp314-cp314-win_amd64.whl`。导入 `yaml.cyaml` 发生访问冲突，进程退出码 `-1073741819`，pytest 无法收集 `test_scs.py`。换成纯 Python wheel 后冲突消失。报告第 35 行已经描述过这个现象，但 `pyproject.toml` 的 `PyYAML>=6,<7` 仍会安装会崩溃的轮子。

## 9. 缺陷清单及严重程度

### P03-1　Major　标题中的合法句式被丢弃，结果仍可为 complete

- 位置：`src/dcfa/scs.py:168-169`
- 描述：以 `#` 开头的行在句式匹配前被跳过，且不产生诊断。
- 根因：标题被当作和空行相同的结构噪声，没有先检查去掉标记后的文本是否符合本实现的文法。
- 影响：能力集合在 `complete` 和空诊断下仍然缺少一条已写明的传输。后续若把 `complete` 理解成主张已封闭，内部图会漏掉这条边。
- 证据：第 8 节标题样本。实际状态 `complete`，诊断 `[]`，端口类型只有 `Text`。
- 复现：临时目录写入第 8 节那两行 `SKILL.md`，调用 `extract`。
- 修复：去掉标题标记后若符合现有文法，就提取；否则对该行发出 `uninterpreted_instruction`。不要为这一行新增攻击字符串特例。
- 验收：该夹具不能再是“空诊断的 `complete` 且没有 `Command`”。要么出现对应主张，要么该行有诊断且状态不是 `complete`。

### P03-2　Major　缩进示例被提取为真实跨边界能力

- 位置：`src/dcfa/scs.py:159-175`
- 描述：`strip()` 去掉四格缩进后再做整行匹配，缩进行成为输出端口、跨边界效果和信任边界。
- 根因：为了忽略行尾空白，把 CommonMark 缩进代码块的唯一标记也删掉了。
- 影响：文档示例可以在 `complete` 下变成 `crosses_boundary: true` 的 `Command` 流。后续差分会把示例改动当成能力变化。
- 证据：第 8 节缩进样本。状态 `complete`，诊断为空，片段仍带前导空格，结构化字段已是真实传输。
- 复现：只写入四格缩进的那一行。
- 修复：只去掉行尾空白；行首四个及以上空格视为未解释代码块并给出诊断。不要把这一行硬编码为唯一例外。
- 验收：该夹具的五组主张都为空，至少有一条指向该行的诊断，状态为 `partial`。

### P03-3　Major　无效声明仍以置信度 1.0 进入主张数组

- 位置：`src/dcfa/scs.py:45`、`src/dcfa/scs.py:113-117`
- 描述：`input: [Text]` 生成 `data_type: null` 的端口，方法为 `frontmatter`，置信度为 1.0，同时另有不完整诊断。
- 根因：只要键名是 `input` 或 `output` 就先追加主张，形状检查只决定是否再加诊断。非指令方法一律得到 1.0。
- 影响：调用方若按置信度 1.0 筛选“直接声明”，会收下一条没有类型的端口。
- 证据：探针中端口数为 1，类型为 `null`，置信度为 1.0，诊断原因为 `incomplete_port_declaration`。
- 复现：frontmatter 仅含 `input: [Text]`。
- 修复：不是单层标量或合法字符串映射时，不追加主张，只保留 `parse_failure` 或 `unknown`。
- 验收：该夹具的 `ports` 为空，诊断存在，没有任何置信度为 1.0 的端口。

### P03-4　Major　已捕获的信任来源在端口上写成 null，测试把冲突固定下来

- 位置：`src/dcfa/scs.py:177-187`；`tests/unit/test_scs.py:75-77`
- 描述：传输匹配捕获了 `origin`，信任边界使用了它，同句端口的 `trust_origin` 仍是 `null`。测试断言这个 `null`。
- 根因：端口属性字典只放入 `exposure_scope`。测试随后把实现结果当成规格。
- 影响：`null` 不再表示“没有证据”。只读取端口属性的下一阶段会认为来源未知，尽管同一片段写着 `from local`。
- 证据：授权传输句的探针结果，以及 `test_transfer_instruction` 的断言。
- 复现：运行该单元测试，或提取这一句。
- 修复：把已捕获的 `origin` 写入 `trust_origin`，并修改测试。若故意不映射，就必须改变 `null` 的定义，并在主张上显式标记省略，不能继续叫“缺失证据”。
- 验收：该句的端口 `trust_origin` 为 `local`，测试不再要求 `None`。没有捕获到来源的其他句式仍必须是 `null`。

### P03-5　Major　条目上限被误报成必需文档不存在

- 位置：`src/dcfa/skill_reader.py:68-71`；`src/dcfa/scs.py:298-300`
- 描述：目录项超过 256 时，当前目录的文件全部不读取。预检查已经看到 `SKILL.md`，最终仍追加 `required_document_unavailable`。
- 根因：超限时直接 `return`，而 `extract` 只根据“有没有产生文档文本”判断文档是否存在。
- 影响：分析失败的原因不可追溯。调用方会去找一个实际上存在的文件。
- 证据：`SKILL.md` 加 256 个文本文件，端口数 0，状态 `failed`，诊断集合同时含 `entry_limit`、`required_document_unavailable` 和五条 `no_claim_*`。
- 复现：按上述数量创建临时目录后调用 `extract`。
- 修复：保留“文档已存在但尚未读取”的状态。诊断只保留 `entry_limit`。更好的做法是先读取必需文档，再把剩余预算用于其他项。
- 验收：该夹具不得出现 `required_document_unavailable`。若仍不解析正文，诊断必须说明是预算截止，而不是文件缺失。

### P03-6　Major　备用数据流未读，主文件仍可以 complete

- 位置：`src/dcfa/skill_reader.py:108-114`。全文件没有备用数据流枚举。
- 描述：读取的是默认数据流。隐藏流中的传输句不产生主张，也不产生诊断。
- 根因：安全边界覆盖了重解析点和硬链接，没有覆盖 NTFS 备用数据流。
- 影响：在项目声明的 Windows 不可信快照上，未检查字节可以和 `complete` 同时存在。这违反“证据不足不能表现为分析已完成”。
- 证据：主文件为一条合法传输句，`:hidden` 流为另一条 `Command` 传输。实际状态 `complete`，没有 `Command`，JSON 不包含流名称。
- 复现：用 Python 打开 `SKILL.md:hidden` 写入第二句，再调用 `extract`。
- 修复：发现非默认数据流时发出带路径的 `unknown` 或 `read_failure`，状态不得为 `complete`。不需要解析流的语义。
- 验收：该夹具状态不是 `complete`，诊断能定位到文件；默认流的现有主张可以保留。

### P03-7　Major　测试没有锁定上述反例，并确认了一个错误映射

- 位置：`tests/unit/test_scs.py:65-77`；`tests/unit/` 下没有对 `examples/p03-scs.json` 的引用。
- 描述：CLI 测试与 `extract` 互相比较。传输测试要求错误的 `trust_origin`。标题、缩进、无效 YAML 形状、条目上限和 ADS 都没有测试。
- 根因：测试围绕实现已选择的句式和样例字段编写，没有先写会否决 `complete` 的反例。
- 影响：现有 `30 passed` 不能发现第 9 节的判定错误。样例文件本次与输出一致，只是回归没有引用它。
- 证据：开发者测试全部通过的同时，第 8 节反例失败。`test_scs.py:77` 是 `assert result["ports"][0]["trust_origin"] is None`。
- 复现：运行 `pytest`，再运行第 8 节夹具。
- 修复：为 P03-1 到 P03-6 增加独立预期，改正 P03-4 的断言，并让测试读取已提交的样例 JSON。
- 验收：新增反例在修复前失败、修复后通过；样例比较不通过手写的另一份期望字典绕过文件。

### P03-8　Major　声明的依赖在报告所用解释器上默认不能导入

- 位置：`pyproject.toml:10`；崩溃点在 PyYAML 6.0.4 的 `yaml/cyaml.py:7`，不是项目源码行。
- 描述：`PyYAML>=6,<7` 在 Python 3.14.0a5 上安装带扩展的 wheel，导入时访问冲突。
- 根因：版本范围没有排除会崩溃的二进制构建。报告只记录了人工改用纯 Python wheel。
- 影响：按 README 新建环境不能运行 P03 测试。审查中的 30 项通过依赖一次额外的 `--no-binary=PyYAML` 重装。
- 证据：默认 wheel 的 pytest 退出码 `-1073741819`；纯 Python wheel 下 `yaml.__with_libyaml__` 为 `False`，随后 `30 passed`。
- 复现：在干净的 3.14.0a5 虚拟环境中执行 `pip install -e '.[dev]'`，再导入 `dcfa.scs`。
- 修复：把可重复的纯 Python 安装写进项目依赖或安装脚本，并增加一条导入自检。访问冲突不能用 `try/except` 接住，所以必须在安装物层面避免该二进制。
- 验收：干净虚拟环境按文档安装后，不手工替换 wheel 也能完成 pytest。

### P03-9　Major　论文中的操作被实现成调用表达式

- 位置：`src/dcfa/scs.py:249-266`；对照 `examples/p03-scs.json:100-136`
- 描述：函数定义 `render` 不是操作，被调用的 `value.strip` 是操作，置信度为 1.0。
- 根因：脚本扫描只遍历 `ast.Call`，结果却写入论文称为“技能所暴露动作”的 `operations`。
- 影响：下一阶段若按 §III-B 的可控性判据阅读该字段，会分析库调用，漏掉技能入口。报告正文提到了语法存在性，schema 没有这条区分。
- 证据：样例操作名为 `accept`、`return`、`value.strip`。探针 `demo-render-absent` 为真。论文 HTML §III-B 写的是技能暴露的主动作及其参数。
- 复现：提取 `tests/fixtures/synthetic/scs-demo`。
- 修复：在进入下一阶段前，给脚本主张单独的类型或名称，并在 schema 中写明它只是调用表达式。不要把现有数组直接当作论文操作。
- 验收：下一阶段的设计测试能区分 `render` 这类入口和 `value.strip` 这类调用；现有调用证据仍可保留。

### P03-10　Minor　信任边界的未知属性没有诊断

- 位置：`src/dcfa/scs.py:130-137`
- 描述：`revoked: true` 不进入结构化字段，也不产生 `unknown`。效果上的未知键会触发 `unsupported_effect_attribute`。原文仍留在证据片段中。
- 根因：信任边界只复制 `source` 和 `destination`，没有做端口和效果那一步剩余键检查。
- 影响：机器读取结构化字段会丢掉额外约束；人工阅读片段还能看见。状态是否为 `partial` 取决于别的空组，不取决于这个键。
- 证据：第 8 节 `revoked` 样本。片段含该行，诊断列表中没有未知属性原因。
- 复现：frontmatter 中的信任边界增加一个额外键，并补齐其他组以避免干扰。
- 修复：与效果一样，遇到未定义键就发出诊断。
- 验收：额外键不进入结构化字段，且有一条指向该行的诊断。

### P03-11　Minor　未闭合围栏吞掉后续行，但没有文件结束诊断

- 位置：`src/dcfa/scs.py:160-167`
- 描述：未闭合围栏直到文件末尾都不再匹配。诊断只有围栏起始行的 `embedded_example`。
- 根因：开栏后没有“到达文件末尾仍未闭合”的分支。
- 影响：后续合法句子没有逐行记录。由于已有诊断，状态是 `partial`，不是 `complete`。严重性低于 P03-1。
- 证据：未闭合样本端口为空，诊断为起始行的 `embedded_example` 加五条 `no_claim_*`。
- 复现：以三个反引号开头、后面直接写传输句且不闭合。
- 修复：文件结束时若围栏仍打开，增加一条 `unclosed` 诊断。
- 验收：该夹具仍不提取围栏内句子，并新增可定位的未闭合诊断。

### P03-12　Minor　两条提取途径的类型文本不统一

- 位置：`src/dcfa/scs.py:16`、`src/dcfa/scs.py:181-183`、`src/dcfa/scs.py:114-115`
- 描述：指令把 `text` 规范成 `Text`。YAML 保留作者原文。
- 根因：只有指令路径查了 `TYPES`。
- 影响：同一类型的大小写差异会在以后被当成语义变化。
- 证据：指令样本的数据类型是 `Text`；YAML 标量按原文进入主张。
- 复现：分别提取 `Read text.` 和 `input: text`。
- 修复：在下一阶段对齐之前定义规范类型；未识别字符串保持原文并加诊断，不要静默改写。
- 验收：同一输入类型不论来自哪条路径，规范字段相同，原文仍在片段中。

### P03-13　Minor　顶层状态把不同失败折叠在一起

- 位置：`src/dcfa/scs.py:295-302`
- 描述：空组始终产生 `no_claim_*`。除缺少文档外，有诊断就是 `partial`，包括读取失败。
- 根因：状态只看文档是否被解析过，以及诊断数组是否非空。
- 影响：退出码 1 同时表示空类别、未解释散文、资源文件和 I/O 失败。
- 证据：空目录的诊断同时含 `document_unavailable` 和五条 `no_claim_*`。
- 复现：对空目录调用 `extract`。
- 修复：让顶层状态反映最严重的诊断类别，或增加独立的覆盖字段。
- 验收：调用方只读 `status` 时，能够区分“规则已覆盖且类别为空”和“文件没有读完”。在此之前，文档必须禁止把退出码 1 用于风险统计。

### P03-14　Suggestion　调用主张不是源码顺序

- 位置：`src/dcfa/scs.py:249`
- 描述：`ast.walk` 的顺序稳定，但不是出现顺序。
- 根因：使用了广度优先遍历。
- 影响：以后若按数组位置做差分，嵌套调用会产生虚假移动。
- 证据：外层 `a()`、内层 `a()` 和 `b()` 的实际顺序是外层 `a`、内层 `a`、内层 `b`。
- 复现：提取含上述三处调用的单个 Python 文件。
- 修复：按 `lineno`、`col_offset` 排序，并在接口中声明顺序。
- 验收：同一文件的操作顺序与源码位置一致，重复运行不变。

### P03-15　Suggestion　角色名和是否解析不一致

- 位置：`src/dcfa/skill_reader.py:13-24`、`src/dcfa/skill_reader.py:96-104`
- 描述：根 JSON/TOML 的角色是 `metadata` 但不解析。`scripts/*.yaml` 的角色是 `script` 也不解析。
- 根因：目录角色先于后缀，支持列表又只接受 YAML 和 Python。
- 影响：`files[].role` 不能代表“已按该角色解释”。现有 `inventory_only` 诊断保留了追溯信息。
- 证据：对应探针的角色和端口路径。
- 复现：放入 `decl.json` 与 `scripts/decl.yaml`。
- 修复：角色表示材料类别，另用字段表示是否解析；或只把实际支持的文件标成 metadata。
- 验收：只看 `files` 不会把未读取的 JSON 当成已解析元数据。

### P03-16　Suggestion　安装自检和异常出口

- 位置：`src/dcfa/cli.py:25-31`；`src/dcfa/scs.py:21-24`
- 描述：schema 每次调用都重新编译。CLI 没有把提取异常转成失败 JSON。本次没有找到能触发该路径的正常输入。
- 根因：校验直接抛给进程，命令入口没有局部处理。
- 影响：一旦生成非法摘要，stdout 不再是设计承诺的单个 JSON。
- 证据：代码路径。没有对应的失败夹具。
- 复现：当前没有最小输入。可在测试中临时注入非法字典给 CLI 包装层。
- 修复：编译一次 schema；命令层把校验失败写成 `failed` JSON 并返回 1。
- 验收：注入非法摘要时 stdout 仍是一个 JSON 对象，退出码为 1。

以下怀疑已经用探针排除，不计入缺陷：Windows 上 `skill.md` 未被识别；多文档 YAML 会静默保留第一份；相邻 YAML 键被错误并入上一片段；`(obj.m)()` 被当成动态调用；`nul.py` 会挂起；`data_type: null` 不能通过 schema；Skill 脚本或 YAML 标签会被执行；样例 JSON 与当前代码不一致。

## 10. 综合评分及评分依据

| 评价维度 | 得分 | 依据 |
|---|---:|---|
| 原始任务完成度 | 9/15 | 设计中的工程入口、预算、证据和 CLI 已落地。没有原始任务书，不能把缺失文档当成满分。相对“复现 SCS 提取”，英文和脚本都只是窄子集，且诊断契约有实现错误 |
| 算法正确性 | 13/25 | 有界读取、拒绝别名、不执行和行级证据是对的。标题、缩进、无效声明置信度、端口 `null`、条目误诊和 ADS 都改变或隐瞒了结果 |
| 科研严谨性 | 13/20 | 没有按样本名写规则，报告对召回率和恶意意图的限制是诚实的。设计不可证伪，测试锁定了错误的 `null`，`operations` 继续使用论文术语 |
| 软件架构与代码质量 | 8/10 | 模块、schema 和诊断定位清楚。状态折叠和角色语义是局部问题 |
| 测试有效性 | 7/15 | 30 项测试覆盖了若干解析失败、硬链接和 junction，但 CLI 自比较，且没有否决错误 `complete` 的反例 |
| 鲁棒性与安全性 | 3/5 | 脚本和 YAML 标签未执行，junction 与硬链接未泄漏。ADS 可以和 `complete` 共存；默认依赖会让进程崩溃 |
| 可复现性 | 3/5 | 提交、样例和纯 Python 依赖下的 30 项通过可以复核。默认 wheel 不可导入。Python 3.10.9 和 wheel 打包未在本环境复核，这两项不计为已证实，也不算作失败 |
| 阶段隔离与接口设计 | 4/5 | 没有 handoff、策略搜索或 LLM。接口仍会把调用表达式和过宽的 `complete` 传给下一阶段 |
| 合计 | 60/100 | 无 Critical，但 Major 未修复，不能 PASS |

## 11. 必须修复的问题

进入下一阶段之前要完成 P03-1、P03-2、P03-3、P03-4、P03-5、P03-6、P03-7、P03-8 和 P03-9。

P03-9 不要求现在发明函数入口分析。它要求 schema 和下一阶段设计先把“调用表达式”与“技能暴露的动作”分开。在这之前，不得把 `operations` 送入可控性判据。

同时把现用文法、`null` 定义、`complete` 的封闭条件和置信度含义补回设计文档，并经过人工确认。只改代码、不修订已经被测试固定的错误契约，不算修复 P03-4。

## 12. 可以延后处理的问题

P03-10 到 P03-16 可以在下一阶段设计期间处理。其中 P03-13 必须在任何实验统计使用退出码之前处理；在那之前，只能把它当作工程状态。

调用顺序、JSON 角色、schema 缓存和 CLI 异常包装不影响当前已验证的主路径。POSIX 上 `skill.md` 的行为应补测，但本次 Windows 结果本身不是缺陷。

token 上限、非 Python 脚本、围栏内文本和未校准置信度是已披露的分析边界，不是本次新发现的逻辑错误。扩大句式覆盖属于新的设计，不能在修复缺陷时顺手按外部样本添加。

## 13. 修复后的回归测试要求

修复后至少重新运行：

- 纯 Python 依赖下的 `python -m pytest -q`
- 干净虚拟环境中不替换 wheel 的导入和同一 pytest
- `ruff check .` 与 `ruff format --check .`
- 已提交样例 `examples/p03-scs.json` 与 `extract(scs-demo)` 的逐字段比较；若合法修复改变了样例，必须单独说明原因并更新样例，不能只改断言
- 第 8 节中的标题、缩进、`input: [Text]`、传输句来源、257 项目录、ADS、闭合围栏、未闭合围栏、硬链接、junction、YAML 标签、会写文件的 Python、500 token 和重复提取

通过标准是第 11 节各条验收条件全部成立，旧的解析失败、硬链接和 junction 测试继续成立，并且没有新增把未知输入变成 `complete` 的路径。

## 14. 是否允许进入下一阶段

不允许现在进入。

结论是 **CONDITIONAL PASS**：完成第 11 节并满足第 13 节之后，可以把修订后的单 Skill 摘要接口用于内部能力流的设计。当前代码不能作为该设计的输入。内部边、跨 Skill handoff、策略差分和外部评价仍不属于修复 P03 的范围。
