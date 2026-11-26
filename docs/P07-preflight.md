# P07 原始 RogueOne 版本和运行前置核验

目标是对 P02 固定源码，用无生命周期脚本的合成 JavaScript 版本对，取得原始分析器的图、域、域间流和增量输出。以论文 §4.2、§4.3 的对象图和域间关系为验收依据。单纯比较文档里的数字不能验证本机运行。[作者论文](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF)

## 版本依据

冻结项目及本地 Git 各引用的路径历史中没有找到 P02 审计或 RogueOne 固定版本。作者公开仓库的 HEAD 查询返回 d92d7de0eedb5754dc4d41b426d45a83715c0bd1，仅作为本次文档核验版本。尚不能确认它是 P02 选定的提交。[官方仓库](https://github.com/columbia/rogueone)

## 已执行的核验

实际 Git 查询、宿主工具版本、固定提交的文档地址及依赖记录见 [preflight.log](../reproduction/P07/preflight.log)。另运行 Get-Command docker,wsl 和 wsl.exe -l -q：当前 PATH 只找到 wsl.exe，其输出提示安装 WSL，未列出 Linux 发行版。宿主工具版本不能作为分析器运行环境版本。

该提交的 dockerfile 以 Ubuntu 22.04 为基础，创建 Python 虚拟环境并调用 fast/install.sh 安装 Python 与 JavaScript 依赖。readme.md 说明完整测试命令，DockerReadme.md 另列双版本信任域测试。仓库包含多类样例，所以尚不能把整个测试目录列为已审核的安全输入。单更新入口接收绝对路径，原始输出为包对目录中的 rogue_one_output.json。后续核验应保存原件，分开检查前后图构建、两版本域归属、域间关系和新增关系；空差分或仅有退出码不足以覆盖这些要求。[固定版运行说明](https://github.com/columbia/rogueone/blob/d92d7de0eedb5754dc4d41b426d45a83715c0bd1/readme.md)

## 历史预检状态（d0f4dd9，运行前）

当时版本前置阻塞。原始项目启动、ODRG、信任域映射、域间流提取、版本差分和结果输出六项均未运行。没有测试计数、运行日志或原始检测 JSON。当前成果属于文档与环境预检，尚未达到部分运行复现；未进行论文方法重实现。无 RogueOne 源码修改、恶意样本执行或包生命周期脚本执行。恢复本阶段需要 P02 已核定的完整 SHA 或其来源记录。

最终运行状态为部分复现，包对入口未写出原生结果。[P07 最终运行报告](P07-report.md)

## 版本确认后的运行设计

用户已确认上述完整 SHA。保留上段作为预检时点记录。使用独立临时目录和虚拟环境，仅取上游分析器代码及声明依赖；合成输入仅含常量字符串处理和标准库路径操作。优先验证原始命令；平台不兼容时分别验证可运行的原始模块，保留错误和实际输出，不将模块调用计为端到端成功。
