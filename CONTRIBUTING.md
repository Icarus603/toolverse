# 贡献指南

感谢你考虑为 Toolverse 项目做出贡献！本文档将指导你如何开始参与和贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
  - [报告 Bug](#报告-bug)
  - [提交功能请求](#提交功能请求)
  - [参与代码贡献](#参与代码贡献)
  - [提交工具数据](#提交工具数据)
  - [分享使用体验](#分享使用体验)
- [环境设置](#环境设置)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交 Pull Request](#提交-pull-request)
- [项目结构说明](#项目结构说明)

## 行为准则

本项目采用了《贡献者公约》行为准则。参与者需要遵守此准则。请查阅 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 了解详情。

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请使用 GitHub Issues 进行报告。报告时请包含：

1. 清晰的 Bug 描述
2. 重现步骤
3. 预期行为与实际行为
4. 相关环境信息（操作系统、Python 版本等）
5. 如可能，附上相关日志或截图

### 提交功能请求

如果你有新的功能建议，请通过 GitHub Issues 提交功能请求，并尽可能详细地描述需求和使用场景。

### 参与代码贡献

如果你想贡献代码：

1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

### 提交工具数据

你可以通过以下方式提交 AI 工具数据：

1. **手动添加**: 直接编辑 `data/processed/tools.yaml` 文件，遵循 [数据模型](docs/data_model.md) 定义
2. **增加爬虫**: 贡献新的爬虫脚本，以收集更多来源的工具数据
3. **Issues 提交**: 如果不熟悉 Git 操作，也可以通过 Issues 提交工具信息

### 分享使用体验

分享你的 AI 工具使用体验是本项目最有价值的贡献之一：

1. 使用 `experience/templates/report_template.md` 模板创建体验报告
2. 将报告保存到对应分类目录（如 `experience/image/tool-name.md`）
3. 提交 Pull Request，分享你的体验

## 环境设置

### 使用 Conda

```bash
# 创建 conda 环境
conda create -n toolverse python=3.10
conda activate toolverse

# 安装依赖
pip install -r requirements.txt
```

### 使用 pip

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 开发流程

1. **爬虫开发**:

   - 爬虫脚本放在 `scripts/crawlers/` 目录下
   - 需提供详细文档说明目标站点和爬取策略
   - 确保数据符合项目数据模型

2. **数据处理**:

   - 数据处理脚本放在 `scripts/processors/` 目录下
   - 确保处理结果符合 YAML 格式规范

3. **分析与可视化**:
   - 分析脚本放在 `notebooks/` 目录中

## 代码规范

- **Python**: 遵循 PEP 8 编码规范
- **YAML**: 遵循项目数据模型定义的结构
- **Markdown**: 使用标准 Markdown 语法撰写文档

提交前请运行以下命令检查代码风格：

```bash
black scripts/
isort scripts/
flake8 scripts/
```

## 提交 Pull Request

1. 确保你的代码通过了代码风格检查
2. 更新相关文档（如有必要）
3. 描述你的更改和工作原理
4. 如涉及大量更改，请先开 Issue 讨论

## 项目结构说明

```
toolverse/
├── data/               # 数据目录
│   ├── raw/            # 爬虫原始数据
│   │   └── ...         # 各来源子目录
│   ├── processed/      # 处理后的数据
│   └── metadata/       # 元数据（分类、标签定义）
├── scripts/            # 脚本目录
│   ├── crawlers/       # 爬虫脚本
│   ├── processors/     # 数据处理脚本
│   └── updaters/       # 自动更新脚本
├── experience/         # 体验报告
│   ├── templates/      # 体验报告模板
│   └── ...             # 各分类子目录
├── notebooks/          # 分析笔记本
├── docs/               # 文档
└── ...                 # 其他项目文件
```

---

再次感谢你考虑为 Toolverse 做出贡献！如有任何问题，请随时在 Issues 中提问。
