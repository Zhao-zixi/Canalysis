# Canalysis 2.0

一个面向 C 代码的函数级分析与可视化工具链：自动扫描指定目录下的 C 函数，基于静态分析与可选 LLM 提示生成结构化 JSON，输出交互式 HTML 报告，帮助快速理解调用关系与行为逻辑。

## 特性概览
- 函数扫描与解析：自动提取函数名、起始行号、函数体内容
- 混合分析引擎：
  - 静态分析（本地可靠）：提取直接调用与进入条件、过滤自调用、合并去重
  - LLM 分析（可选）：严格 JSON 输出，补充更精细的语义与归纳
- 条件表达式提取：
  - 标准化为括号内表达式（不含 `if` 与外层括号）
  - 识别守卫式早返回并对后续调用条件取反（如 `len == 0` → 后续为 `len != 0`）
  - 支持跨行与嵌套括号的平衡解析
- 可视化报告：
  - 全局图与局部聚焦视图（基于 Cytoscape.js + Dagre）
  - 右侧详情展示：Summary、Location、Calls（下游）、Callers（上游）
  - 中英文切换、搜索过滤、邻居展开/收起
- 结果缓存：
  - 持久化保存 LLM 成功结果（按文件路径 + 函数名 + 行号 + 内容哈希）
  - 二次运行跳过未变更函数，加速端到端流程
- 示例工程：`examples/linux_serial_demo`（内核/用户态串口演示）

## 目录结构
```
Canalysis2.0/
├─ examples/               示例工程（kernel/user）
├─ llm/                    分析引擎（静态与LLM逻辑）
│  └─ analyze_functions.py
├─ scripts/                函数扫描脚本
│  └─ scan_c_functions.py
├─ visualization/          报告生成与前端资源
│  ├─ generate_report.py
│  └─ libs/                Cytoscape/Dagre等静态库
├─ main.py                 端到端入口（扫描→分析→报告）
└─ README.md               项目说明
```

## 安装与环境
- 依赖：Python 3.9+（Windows 已测试）
- 安装依赖：
  - 若需要联网加载 LLM（可选），请在 `llm/analyze_functions.py` 中配置好 `BASE_URL`、`MODEL`、`API_KEY`
  - 前端库已打包在 `visualization/libs/`

## 快速开始
- 端到端生成报告（静态分析模式）：
  - `python main.py --target examples/linux_serial_demo --mode fallback --output visualization/report.html`
- 使用 LLM 同步模式（会写入缓存）：
  - `python main.py --target examples/linux_serial_demo --mode sync --output visualization/report.html`
- 使用 LLM 异步模式（会写入缓存）：
  - `python main.py --target examples/linux_serial_demo --mode async --max-concurrency 5 --output visualization/report.html`
- 清理旧输出（不清除缓存）：
  - `python main.py --target examples/linux_serial_demo --mode fallback --output visualization/report.html --clean`
- 保留中间 JSON：
  - `python main.py --keep-json`

### 参数说明
- `--target` 目标源码目录（默认 `examples/linux_serial_demo`）
- `--mode` 分析模式：`fallback`（静态）、`sync`（LLM 同步）、`async`（LLM 异步）
- `--max-concurrency` 异步并发上限（默认 5）
- `--output` 报告输出路径（默认 `visualization/report.html`）
- `--clean` 清理旧报告与中间分析 JSON（不影响缓存）
- `--keep-json` 保留中间 JSON `llm/function_analysis.json`

## 分析引擎
- 静态分析（关键逻辑）
  - 调用提取：识别形如 `callee(...)` 的直接调用，过滤关键字与自调用
  - 条件解析：
    - 提取 `if(...)` 括号内的表达式（跨行与嵌套括号）
    - 若调用在 `if` 块内，使用该表达式；若前置为无花括号守卫式早返回，则对表达式取反
    - 无条件时标注为 `unconditional`
  - 去重与合并：对 `(callee, condition)` 去重
- LLM 分析（可选）
  - 严格 JSON Schema：
    - `file_path`, `function_name`, `line_number`, `content`, `origin`, `summary`, `calls`, `confidence`, `notes`
  - 提示规范：只保留函数体内的直接、可达调用；条件输出为表达式本身；早返回取反；避免冗余文本
  - 异常回退：LLM 调用失败时自动回退到静态分析

## 可视化报告
- 全局视图：展示所有函数以及有向调用边
- 局部聚焦：以选中函数为中心，展开上游 `Callers` 与下游 `Calls`
- 详情面板：
  - `Summary` 功能摘要
  - `Location` 代码位置 `file_path:line_number`
  - `Calls` 下游调用（带条件表达式）
  - `Callers` 上游调用方（带触发条件）
- 交互：搜索过滤、展开/收起邻居节点、语言切换（中/英）

## 缓存机制
- 缓存文件：`llm/function_analysis_store.json`
- 缓存键：`<file_path>:<function_name>:<line_number>`
- 变更检测：对 `content` 计算 `sha1` 前 16 位作为哈希；哈希一致则跳过分析直接复用
- 写入时机：仅在 `sync`/`async` 模式且 `notes` 不包含 `fallback_static_analysis` 时持久化保存

## 示例工程
- `examples/linux_serial_demo` 包含内核与用户态示例：串口收发、状态查询、IOCTL 等典型接口
- 用于验证条件取反、可达路径与双向调用关系的可视化效果

## 常见问题
- LLM 不可用：
  - 使用 `--mode fallback` 保证端到端可用性
  - 网络或服务异常时自动回退到静态分析
- 报告空白或库缺失：
  - 确认 `visualization/libs` 下的 `cytoscape.min.js`/`dagre.min.js`/`cytoscape-dagre.min.js` 存在
- Windows 路径与编码：
  - 所有输出路径统一为 `/` 分隔，避免前后端解析差异

## 开发指南
- 函数扫描：`scripts/scan_c_functions.py`
- 分析引擎：`llm/analyze_functions.py`
  - `extract_calls_with_conditions(...)` 负责调用与条件解析
  - 自调用过滤、条件取反与跨行括号平衡
- 报告生成：`visualization/generate_report.py`
  - 注入 JSON 数据与静态库，生成 `report.html`

## 许可与致谢
- 前端可视化基于 Cytoscape.js 与 Dagre（MIT 许可）
- 代码示例基于自建演示工程

## 路线图
- 条件控制流增强：支持 `else/else if` 与更复杂 CFG
- 支持更多语言与跨文件调用分析
- 报告交互增强：按模块/文件聚合、性能优化

---
如需将分析切换到 LLM 模式并持久化缓存，请在 `llm/analyze_functions.py` 配置好模型与密钥，并通过 `--mode sync/async` 运行 `main.py`。欢迎提交反馈与改进建议。
