# P07 原始 RogueOne 运行验证

**验收结论为部分复现。** 在同一个无害合成版本对上，原始文件分析入口和原始域差分函数给出了可核对的新增关系。原始包对入口未完成。同一方法的两个入口有不同的运行证据，不能合并为一次端到端成功。

## 来源与设置

本次目标是验证 RogueOne 程序级方法的实际运行链。依据为论文 §4.2–4.3、固定提交中的 rogue_one_runner.py、fast/dataflow/extraction.py 和 fast/dataflow/trust_domains.py。P02 记录在当前仓库未找到，本次使用用户确认的上游提交 d92d7de0eedb5754dc4d41b426d45a83715c0bd1。设计先于运行提交于 d0f4dd9。环境为 Windows 10.0.26300、独立 Python 3.10.9 venv、Node v24.15.0、npm 11.12.1 和 Git 2.50.1.windows.1。Python 与 npm 顶层安装版本分别见 python-packages.txt、npm-packages.txt。[作者论文](https://yinzhicao.org/RogueOne/RogueOne-ICSE24.PDF) · [固定版本](https://github.com/columbia/rogueone/tree/d92d7de0eedb5754dc4d41b426d45a83715c0bd1) · [预检与设计](P07-preflight.md)

运行使用独立临时目录，源码按路径从提交归档提取，避免检出样本目录中的 Windows 非法文件名。仅安装分析器依赖，npm 禁用安装脚本。输入由 run_pair.py 写入两个新目录，仅含 package.json 和 index.js。旧版导出常量 demo.txt，新版导出标准库 path.basename 对该常量的结果。文件模式直接静态分析两个入口文件。此设计仅检验静态关系能否出现，不支持推断恶意意图。

## 验证项与证据

| 项目 | 实际观察 | 范围 |
|---|---|---|
| 项目启动 | 帮助入口输出参数，分析器能处理两个指定 JS 文件 | CLI 启动通过，包对流程受阻 |
| ODRG | extract_idg 返回旧版 572 节点、477 边，新版 836 节点、1377 边。原始 sanitize_and_export 过滤 AST 后分别导出 0/0、233/667 | 文件模式通过，JSON 中 objects 是图的总节点数 |
| 信任域 | td_rel_map 运行后新版含 path、:local:demo.txt 等域标签；旧版无标签 | 新版有非空证据，标签本身不证明执行过相应行为 |
| 跨域流 | 新版返回 (:local:demo, path)，附两条节点序列，旧版无关系 | 已核对序列内节点存在于新版 GraphML |
| 版本差分 | 原始 flagged_single_local_rels_from_tuples 返回 (:local, path) | 文件模式通过，归一化后关系名与输入关系有别 |
| 原始检测结果文件 | 包对入口警告 No files processed，随后 mem_info 读取 Windows psutil.pmem 缺失的 shared 属性并抛出 AttributeError | 未生成 rogue_one_output.json，模块返回值另外保存 |

初次函数体形式的样例没有得到域间关系，返回值保留在 results/。顶层语句样例的文件模式产物在 top-level/。两组是不同输入。文件模式日志中的 Detection: failed 是底层分析器字段，域间差分另见原始函数返回值。包对运行警告的具体成因尚未定位。即使解决内存遥测异常，也仍须证实包对入口实际处理了两个文件。[运行日志、调用脚本和结果](../reproduction/P07/)

## 模块接口、命令和复核

run_pair.py 接收原始源码目录和全新包对目录，构造合成输入后调用 process_package_pair_given_names，保留异常。probe_modules.py 接收源码目录、已存在的合成包对、输出目录，按文件调用原始分析器，保存两个 GraphML 和包装成 JSON 的原函数返回值。check_record.py 独立读取保存的结果验证关系、见证节点和差分。

以下是主要运行命令，路径以变量统一表示。pair3 是本次已经使用的输入目录；重新生成须换用新目录。

~~~powershell
$d = Join-Path $env:TEMP 'dcfa-p07-d92d7de'
$p = Join-Path $d 'venv/Scripts/python.exe'
$src = Join-Path $d 'code'
D:/Anaconda/python.exe -S -m venv "$d/venv"
& $p -m pip install -r "$src/fast/requirements.txt"
npm.cmd install --prefix "$src/fast/esprima-csv" --ignore-scripts --no-audit --no-fund --no-package-lock
& $p "$src/rogue_one_runner.py" --help
& $p reproduction/P07/run_pair.py $src "$d/pair3"
& $p reproduction/P07/probe_modules.py $src "$d/pair3" reproduction/P07/top-level
& $p reproduction/P07/check_record.py
~~~

独立复核在实验 venv 中通过，输出为旧版 0 节点 0 边、新版 233 节点 667 边，关系和差分断言通过。宿主默认 python 的 site 初始化遇到编码错误，复核结果来自实验 venv。文件清单包括本报告、预检设计、reproduction/P07 下的调用与校验脚本、安装版本清单、运行日志、解析器输出和两组合成输入的结果。未修改上游分析方法，未运行官方混合样本测试集。完整复现仍需在支持原始目录格式和遥测接口的环境中，让包对入口处理这两个合成包并取得原生结果文件。本阶段停在 P07。
