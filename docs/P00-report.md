# P00 验收记录

设计提交 01c81b8 先于代码实现。初始工作区为空，AGENTS.md 来自用户提供的全局规范。研究目的、设计假设与模块契约见 P00-design.md。本阶段依据项目规范搭建基础设施，无论文算法、风险输出或外部评价。

## 变更与接口

| 文件 | 用途 |
|---|---|
| AGENTS.md、README.md、pyproject.toml、.gitignore、.gitattributes | 项目约束、安装、开发工具与版本控制 |
| docs/P00-design.md、docs/P00-report.md、docs/templates/stage.md | 设计、验收、阶段研究模板 |
| third_party/README.md、third_party/sources.json | 固定版本登记契约及空清单 |
| src/dcfa/__init__.py、__main__.py、cli.py | 包与 CLI 入口，main(argv) 返回退出码 |
| src/dcfa/registry.py | validate(bytes) 返回条数或抛出 InvalidRegistry；inspect_registry(Path) 返回带摘要的状态字典 |
| src/dcfa/runs.py | record(root, result) 返回已发布记录的路径，文件系统错误抛出 OSError |
| tests/conftest.py、tests/fixtures/synthetic/empty-registry.json | 按显式名称加载开发夹具 |
| tests/unit/test_{cli,fixtures,registry,runs}.py | 独立覆盖接口、成功路径与失败路径 |

## 实测

Windows，Python 3.14.0a5，pytest 9.2.0，Ruff 0.17.6。下列命令使用项目 .venv/Scripts 中的可执行文件。

| 命令 | 结果 |
|---|---|
| python -m pytest -q | 18 passed in 0.21s |
| ruff check . | All checks passed! |
| ruff format --check . | 15 files already formatted |
| dcfa check-sources | 退出 0，status=ok，count=0 |
| dcfa record-run | 退出 0，运行号 9d14b7917a53444baff785697da45029 |

运行记录位于 runs/9d14b7917a53444baff785697da45029/record.json。空登记只证明基础设施可操作。格式校验不核实远端来源，开发数据边界依赖可信项目工作树与评价资料分离保管。未读取 SkillUpdate-Pilot 算法或评价集。仅验证上述解释器环境。

## 阶段门控

P00 工程验收项通过，待人工确认。P01 的依赖是人工放行、可核实的 KnotScryer 论文和相应原始实现及固定版本、针对单 Skill 的范围定义和先于实现提交的设计。若原始实现不可获得，需要明确记录复现边界。
