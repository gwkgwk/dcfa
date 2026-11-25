# P03 单 Skill SCS 验收记录

目标为从一个静态 Skill 快照提取带来源的能力事实。设计先行提交 e220fcc。输入约束、返回类型及退出码见 [接口设计](P03-design.md)，完整示例见 [独立 SCS JSON](../examples/p03-scs.json)。

## 与论文的对应关系

| 论文定位 | 实现位置 | 可核验的对应关系 |
|---|---|---|
| §II-A，图 4 | skill_reader.scan / role | 识别规范文档、结构化元数据、脚本与资源。先核验根目录和必需文档，超限与不可读取条目带路径报告 |
| §III-B 的 YAML 解析 | Material.metadata / declaration | 读取 YAML 节点及行号，不构造用户对象。input/output、effect、context_exposure、trust_boundary 是本地声明约定。输入／输出共同构成一类 |
| §III-B 的语言启发式 | Material.document | 完整匹配有限的英文指令句；显式传输陈述可产生操作、端口、效果、暴露和跨域主张。缺少授权信息时保留 null |
| §III-B 的脚本静态扫描 | Material.python | Python AST 记录可命名的调用表达式和实参源码；程序事实仅指语法上存在。动态调用目标单列 unknown |
| §III-B 的证据 | Material.add；scs.schema.json | 每条主张内联相对路径、原文行段、片段、方法和分值。1.0 表示直接语法或声明，0.5 表示句式推断。分值未经校准，不能解释为正确概率 |
| §III-E2 | P01 已界定为链级验证 | 单 Skill 输出在 SCS 阶段结束，无模型调用、提示词或运行时工具接口 |

原文依据见 [P01 审计](reproduction/knotscryer_analysis.md) 和 [论文 §III-B](https://arxiv.org/html/2610.32155v1#S3.SS2)。字段拼写、JSON Schema、字段缺证时的 null、诊断分类、英文句式和 AST 支持范围均为重实现选择。

## 接口与文件

- src/dcfa/skill_reader.py 提供 scan(root, issue)，产生清单和有界文本。src/dcfa/scs.py 的 extract(Path) 返回已校验的 dict；validate(dict) 在结构非法时抛出 JsonSchemaValueException。
- src/dcfa/cli.py 新增 dcfa scs DIRECTORY，标准输出为单个 JSON；错误或不完整仍可保存结构化结果。pyproject.toml 声明分析器自身依赖并将 src/dcfa/scs.schema.json 随包发布。
- tests/conftest.py 登记合成目录；tests/fixtures/synthetic/scs-demo 内含 SKILL.md、scripts/format.py、resources/layout.txt。tests/unit/test_skill_reader.py 和 test_scs.py 验证读取、解析、证据、异常、Schema 和 CLI。
- docs/P03-design.md、本文与 examples/p03-scs.json 分别保存设计、验收与实际输出。

## 实测

| 环境或入口 | 命令或核验 | 结果 |
|---|---|---|
| Windows，Python 3.10.9 | python -m pytest -q | 30 passed in 0.68s |
| Windows，Python 3.14.0a5，纯 Python 版 PyYAML | python -m pytest -q | 30 passed in 0.59s |
| Ruff | ruff check . / ruff format --check . | 检查及格式通过 |
| 构建 | python -m pip wheel --no-build-isolation --no-deps . -w 临时目录 | 构建成功，归档含 dcfa/scs.schema.json |
| 安装入口 | dcfa scs tests/fixtures/synthetic/scs-demo | 退出 1，partial。JSON 与保存的独立样例逐字段一致 |

首次在 3.14 早期预览解释器上导入原生依赖时出现访问冲突。最终方案使用 fastjsonschema 2.22.3；该预览环境的 PyYAML 6.0.4 使用纯 Python 构建。稳定版 3.10.9 的独立虚拟环境使用常规安装验证。

示例保留 4 个端口主张、1 个效果、3 个操作、1 项上下文暴露、1 项信任边界及 3 条未知诊断。声明端口与自然语言端口分别带证据；这些数值是主张条数，未做实体合并。没有以测试集设计能力类别。

## 分析边界

仅适用于调用方控制的静止、已脱敏、本地只读快照。文件扩展名和所在目录用于角色识别，资源与不支持的脚本登记为 inventory_only。读取预算为 256 项、12 层目录边界、32 KiB/文件、256 KiB 内容总量。Python 单文件还限制为 500 个 token，单份证据片段上限为 2048 个字符。非 UTF-8、含别名或标签的 YAML、无法解析的脚本和未覆盖的语句均可造成信息缺口。complete 只表示当前提取规则运行完成且无诊断，字段 null 仍表示相应属性无证据。测试不衡量语义召回率，也不能证明运行时执行、实际授权或恶意意图。P03 工程项已验证，等待人工审核。
