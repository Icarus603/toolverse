# Toolverse 数据模型

本文档描述了 Toolverse 项目中用于存储 AI 工具信息的数据模型结构。

## 工具数据结构 (YAML)

每个 AI 工具在 `tools.yaml` 中使用以下结构存储：

```yaml
- id: "unique-tool-id" # 唯一标识符
  name: "工具名称" # 工具显示名称
  url: "https://tool-website.com" # 工具官方网站
  description: "工具简短描述" # 简短描述（1-2句话）
  detailed_description: | # 详细描述（支持多行）
    这里是工具的详细描述，可以包含多行文本，
    介绍工具的主要功能和用途。

  # 分类信息
  category: "text" # 主分类 (text, image, video, audio, workflow, robotics, other)
  subcategory: "writing" # 子分类
  tags: # 标签列表
    - "gpt"
    - "writing-assistant"
    - "productivity"

  # 技术细节
  api_available: true # 是否提供API
  open_source: false # 是否开源
  github_repo: "username/repo" # GitHub仓库 (如果开源)
  tech_stack: # 技术栈
    - "GPT-4"
    - "React"

  # 价格信息
  pricing:
    model: "freemium" # 计费模式 (free, freemium, paid, subscription)
    has_free_tier: true # 是否有免费层级
    free_tier_limits: "每月500次请求" # 免费层级限制描述
    price_range: "$$" # 价格范围 ($: <10, $$: 10-50, $$$: 50-200, $$$$: >200)
    pricing_url: "https://example.com/pricing" # 价格页面链接

  # 使用体验 (由贡献者填写)
  experience:
    reviewer: "username" # 评测者GitHub用户名
    date: "2023-06-15" # 评测日期
    ease_of_use: 4 # 易用性 (1-5)
    effectiveness: 5 # 有效性 (1-5)
    reliability: 3 # 可靠性 (1-5)
    pros: # 优点列表
      - "响应速度快"
      - "界面简洁直观"
    cons: # 缺点列表
      - "高级功能需要付费"
      - "偶尔出现服务中断"
    review: | # 详细评测
      使用该工具的详细体验报告。可以包含多行文本，
      描述工具的使用场景、优势和不足。
    rating: 4.5 # 总体评分 (1-5)
    experience_report: "experience/text/tool-name.md" # 详细体验报告链接

  # 媒体资源
  media:
    logo: "https://example.com/logo.png" # Logo URL
    screenshot: "https://example.com/screenshot.png" # 截图URL
    demo_video: "https://youtube.com/watch?v=xxx" # 演示视频链接

  # 元数据
  added_date: "2023-06-10" # 添加日期
  updated_date: "2023-06-15" # 最后更新日期
  popularity: # 流行度指标
    github_stars: 1200 # GitHub星数 (如果开源)
    monthly_visits: 50000 # 月访问量 (如果能获取)

  # 来源信息
  source:
    type: "crawler" # 数据来源类型 (manual, crawler)
    url: "https://reddit.com/r/..." # 爬取来源URL
    date: "2023-06-10" # 爬取日期
```

## 体验报告结构 (Markdown)

每个工具的详细体验报告存储在 `experience/[category]/[tool-name].md` 文件中，使用以下结构：

```markdown
# [工具名称] 使用体验报告

**评测者:** [GitHub 用户名]  
**评测日期:** [YYYY-MM-DD]  
**工具版本:** [版本号或日期]

## 工具简介

[简短介绍工具的主要功能和用途]

## 使用场景

[描述测试工具的具体场景和任务]

## 优点

- [优点 1]
- [优点 2]
- ...

## 缺点

- [缺点 1]
- [缺点 2]
- ...

## 使用体验

[详细描述使用过程中的体验，包括 UI/UX、功能完整性、性能、稳定性等]

## 与类似工具对比

[与同类工具的对比分析]

## 总结

[总结性评价，包括推荐使用场景和总体评分]

## 截图/视频

[使用过程的截图或视频链接]
```

## 元数据定义

### 分类体系

主分类:

- `text`: 文本相关工具
- `image`: 图像相关工具
- `video`: 视频相关工具
- `audio`: 音频相关工具
- `workflow`: 工作流自动化工具
- `robotics`: 机器人相关工具
- `multimodal`: 多模态工具
- `other`: 其他类型工具

子分类根据主分类不同而变化，详见 `data/metadata/categories.yaml`。

### 标签系统

标签用于更细粒度地描述工具特性，可以跨分类使用。常用标签包括：

- 技术相关: `gpt`, `stable-diffusion`, `llama`, `bert` 等
- 功能相关: `summarization`, `translation`, `generation`, `editing` 等
- 行业相关: `education`, `healthcare`, `finance`, `entertainment` 等
- 特性相关: `open-source`, `api-available`, `self-hosted`, `cloud-based` 等

完整标签列表见 `data/metadata/tags.yaml`。

## 数据验证规则

所有工具数据必须满足以下规则：

1. `id` 必须全局唯一
2. `name`, `url`, `description`, `category` 为必填字段
3. `url` 必须为有效 URL
4. `category` 必须为预定义的主分类之一
5. 如果设置 `open_source` 为 `true`，则 `github_repo` 必须提供
6. 评分必须在 1-5 之间，可以使用小数

详细验证规则在 `scripts/processors/data_validator.py` 中实现。
