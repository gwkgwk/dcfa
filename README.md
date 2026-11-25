# DCFA

单个 Agent Skill 的版本更新研究。P00 提供工程自检。在本项目根目录的 PowerShell 中运行：

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python scripts/install_dev.py
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\dcfa check-sources
.\.venv\Scripts\dcfa record-run
```

## 数据边界

开发测试只从 tests/fixtures/synthetic 的显式名单读取静态合成夹具，也可在独立临时目录构造合成输入。新增夹具需人工确认来源并更新 tests/conftest.py。pytest 默认发现范围为 tests/unit。外部评价资料由评价方保存在仓库外独立受控位置，开发环境不挂载、不配置其路径。冻结算法、锁定 Git 提交并经人工批准后方可开展独立评价。Git 忽略规则只防误提交，操作系统权限由环境管理者配置。

## 命令与状态

check-sources 读取项目维护者管理的 third_party/sources.json，record-run 将同一项校验及其结果保存到 runs/<运行号>/record.json。请使用可信项目工作树与普通本地目录。两命令标准输出均为 JSON，运行日志写标准错误。成功退出 0，校验或写入失败退出 1，参数错误退出 2。status 为 ok 或 failed，只描述工程操作。error 为 null 或机器可读错误码；registry_io 与 record_io 分别表示读取清单和发布记录失败，其余错误码定位格式校验。runs 由 Git 忽略。

设计及验收模板见 docs/templates/stage.md。第三方版本登记规范见 third_party/README.md。
