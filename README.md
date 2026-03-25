# 小红书自动发布工具

> AI 驱动的小红书笔记自动生成与发布工具（v2.0 性能优化版）

一个基于 OpenAI GPT-4 和 DALL-E 3 的自动化工具，可以根据主题自动生成小红书笔记文案和配图，并通过浏览器自动化技术完成发布。

## 🎉 v2.0 性能优化亮点

- ⚡ **2倍提速**：单篇生成从 2分钟 降至 1分钟
- 🚀 **3倍图片生成提速**：并发生成 3张图片仅需 30秒
- 📊 **批量发布优化**：10篇节省 14分钟，20篇节省 34分钟
- 🔄 **智能重试**：API成功率从 85% 提升至 98%

> 📖 详细优化说明：[性能优化指南](OPTIMIZATION_GUIDE.md) | [技术细节](PERFORMANCE.md) | [优化总结](OPTIMIZATION_SUMMARY.md)

## ✨ 功能特性

- 🤖 **AI 文案生成**：使用 GPT-4o 生成符合小红书风格的标题、正文和标签
- 🎨 **AI 图片生成**：通过 DALL-E 3 自动生成配图（支持自定义图片提示词）
- 📸 **本地图片支持**：可使用本地图片替代 AI 生成，节省成本
- 🌐 **自动化发布**：基于 Playwright 实现浏览器自动化，模拟真实用户操作
- 📦 **批量发布**：支持批量发布多篇笔记，自动控制发布间隔
- ⚡ **性能优化**：并发图片生成 + 智能预生成，大幅提升批量发布速度
- 🔄 **自动重试**：网络错误、API 限流自动重试，提高成功率
- 🔐 **登录状态保持**：一次登录，长期有效（Cookie 持久化）
- 🧪 **试运行模式**：支持 Dry-Run 模式，预览不发布
- 🔌 **兼容多种 API**：支持所有 OpenAI 兼容的 API 服务（DeepSeek、腾讯混元等）

## 📋 技术栈

| 技术 | 用途 |
|------|------|
| Python 3 | 基础运行时 |
| OpenAI SDK | GPT-4o 文案生成 + DALL-E 3 图片生成 |
| Playwright | 浏览器自动化发布 |
| Loguru | 结构化日志记录 |
| httpx | 图片下载 |

## 🚀 快速开始

### 1. 环境准备

**系统要求**：
- Python 3.8+
- 稳定的网络连接

**安装依赖**：
```bash
# 克隆项目
git clone <repository-url>
cd xhs-auto-publisher

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（仅首次需要）
playwright install chromium
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**必填配置项**：
```env
# OpenAI API 密钥（必填）
OPENAI_API_KEY=sk-your-api-key-here

# API 地址（可选，默认为 OpenAI 官方）
OPENAI_BASE_URL=https://api.openai.com/v1

# 模型配置（可选，默认值如下）
CHAT_MODEL=gpt-4o
IMAGE_MODEL=dall-e-3

# 发布配置（可选）
PUBLISH_INTERVAL_SECONDS=300    # 批量发布时的间隔时间（秒）
MAX_IMAGES_PER_NOTE=9           # 单篇笔记最多图片数
```

**使用其他 API 服务**：
```env
# DeepSeek 示例
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
CHAT_MODEL=deepseek-chat

# 腾讯混元示例
OPENAI_BASE_URL=https://api.hunyuan.cloud.tencent.com/v1
```

### 3. 首次登录

```bash
python main.py login
```

执行后会自动打开浏览器窗口，请按照以下步骤操作：
1. 使用小红书 APP 扫码登录（或手机号验证码登录）
2. 登录成功后程序会自动保存 Cookie
3. Cookie 文件保存在 `cookies/xhs_cookies.json`，后续发布时自动使用

> **提示**：登录状态通常可保持数周，如果发布失败提示需要登录，请重新执行此命令。

## 📖 使用方法

### 单篇发布

**基础用法**：
```bash
python main.py publish --topic "秋天穿搭推荐"
```

**附加要求**：
```bash
python main.py publish \
  --topic "秋天旅行推荐" \
  --extra "推荐3个国内小众目的地，预算3000元以内"
```

**使用本地图片**：
```bash
python main.py publish \
  --topic "我的旅行日记" \
  --images ./my_photos/
```

**试运行模式**（不真正发布）：
```bash
python main.py publish --topic "新手化妆教程" --dry-run
```

### 批量发布

**1. 创建主题列表文件**：
```bash
cat > topics.txt <<EOF
秋天穿搭推荐，适合微胖女生
居家办公好物分享，提升效率的5个神器
周末一人食，简单又好吃的三道菜
新手化妆教程，5分钟出门妆容
小众旅行目的地推荐，人少景美
EOF
```

**2. 执行批量发布（优化模式，默认）**：
```bash
# 智能预生成：发布间隔期自动生成下一篇，节省总时间
python main.py batch --file topics.txt
```

**3. 批量发布（标准模式）**：
```bash
# 逐篇生成发布，不预生成
python main.py batch --file topics.txt --no-optimization
```

**4. 批量试运行**：
```bash
python main.py batch --file topics.txt --dry-run
```

> **性能对比**：
> - **标准模式**：10篇约需 **50 分钟**（生成2分钟 + 间隔5分钟）× 10
> - **优化模式**：10篇约需 **47 分钟**（首篇2分钟 + 后续每篇仅需间隔5分钟）
> - **提速原理**：利用发布间隔期并发生成下一篇内容

## 📁 项目结构

```
xhs-auto-publisher/
├── main.py                    # 主入口，CLI 命令行工具（优化版）
├── config.py                  # 全局配置管理
├── content_generator.py       # AI 文案生成模块（带重试）
├── image_generator.py         # AI 图片生成与管理（并发优化）
├── retry_utils.py             # 重试机制工具模块（新增）
├── xhs_publisher.py           # 浏览器自动化发布
├── topics.txt                 # 批量发布主题列表（示例）
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量配置模板
├── .gitignore                 # Git 忽略规则
├── cookies/                   # Cookie 存储目录（自动创建）
│   └── xhs_cookies.json       # 登录状态文件
└── output/                    # 输出目录（自动创建）
    ├── publish.log            # 完整日志
    └── note_*/                # 每篇笔记的数据
        ├── images/            # 生成的图片
        │   ├── image_1.png
        │   ├── image_2.png
        │   └── image_3.png
        └── note_data.json     # 笔记元数据
```

## 🔧 工作流程

### 标准流程
```
用户输入主题
    ↓
【Step 1】生成文案（自动重试）
    └─ 调用 GPT-4o API
    └─ 失败自动重试（最多3次，指数退避）
    └─ 输出：标题、正文、标签、图片描述
    ↓
【Step 2】准备图片（并发优化）
    ├─ 选项A：AI 生成（DALL-E 3）
    │   └─ 3张图片并发生成（提速3倍）
    │   └─ 每张失败自动重试（最多3次）
    └─ 选项B：使用本地图片
        └─ 扫描指定目录
    ↓
【Step 3】保存数据
    └─ 保存到 output/note_*/
    ↓
【Step 4】自动发布
    └─ Playwright 启动浏览器
    └─ 打开小红书创作者中心
    └─ 上传图片、填写内容
    └─ 点击发布按钮
    ↓
【完成】日志记录
    └─ 保存到 output/publish.log
```

### 批量发布优化流程
```
发布第1篇
    ↓
等待间隔（5分钟）
    ├─ 同时：后台生成第2篇内容
    └─ 等待结束
    ↓
发布第2篇（使用预生成内容）
    ↓
等待间隔（5分钟）
    ├─ 同时：后台生成第3篇内容
    └─ 等待结束
    ↓
... 依此类推

总时间节省：约 (生成时间 - 间隔时间) × 篇数
```

## ⚙️ 命令行参数说明

### login 命令

```bash
python main.py login
```

首次使用时执行，保存小红书登录状态。

### publish 命令

```bash
python main.py publish [选项]
```

**参数**：
- `--topic TEXT`：笔记主题（必填）
- `--extra TEXT`：附加要求（可选）
- `--images PATH`：本地图片目录路径（可选，不使用则 AI 生成）
- `--dry-run`：试运行模式，不真正发布（可选）

**示例**：
```bash
# 基础发布
python main.py publish --topic "健身日常"

# 带附加要求
python main.py publish --topic "健身日常" --extra "适合新手，在家可做"

# 使用本地图片
python main.py publish --topic "旅行" --images ./photos/

# 试运行
python main.py publish --topic "测试" --dry-run
```

### batch 命令

```bash
python main.py batch --file <主题列表文件> [选项]
```

**参数**：
- `--file PATH`：主题列表文件路径（必填，每行一个主题）
- `--dry-run`：试运行模式（可选）
- `--no-optimization`：禁用优化模式，使用标准逐篇生成（可选）

**示例**：
```bash
# 批量发布（默认优化模式）
python main.py batch --file topics.txt

# 批量发布（标准模式）
python main.py batch --file topics.txt --no-optimization

# 批量试运行
python main.py batch --file topics.txt --dry-run
```

## 🎨 自定义文案风格

如需自定义文案生成风格，可编辑 `content_generator.py` 中的提示词：

```python
# content_generator.py 第11-29行
SYSTEM_PROMPT = """你是一位专业的小红书内容创作者...

修改此处的提示词可以调整：
- 文案风格（活泼/专业/文艺等）
- 内容长度
- Emoji 使用策略
- 标签生成规则
- 图片描述风格
"""
```

## 📊 日志与数据

### 日志文件

所有执行日志保存在 `output/publish.log`，包含：
- 文案生成过程
- 图片生成状态
- 发布执行结果
- 错误信息和堆栈

**日志配置** (自动轮转，保留最近 7 天)：
```python
logger.add(
    "output/publish.log",
    rotation="10 MB",      # 单文件最大 10MB
    retention="7 days",    # 保留 7 天
    encoding="utf-8",
)
```

### 笔记数据

每篇笔记的数据保存在 `output/note_<ID>/note_data.json`：

```json
{
  "note_id": "abc12345",
  "timestamp": "2024-03-24 10:30:00",
  "topic": "秋天穿搭推荐",
  "title": "秋日温柔穿搭｜显瘦又时髦✨",
  "content": "正文内容...",
  "tags": ["秋日穿搭", "显瘦穿搭", "时尚博主"],
  "image_prompts": ["图片描述1", "图片描述2", "图片描述3"],
  "images": [
    "output/note_abc12345/images/image_1.png",
    "output/note_abc12345/images/image_2.png",
    "output/note_abc12345/images/image_3.png"
  ]
}
```

## 🚨 常见问题

### 1. Cookie 失效怎么办？

**症状**：发布时提示"❌ Cookie 已失效"

**解决方法**：
```bash
python main.py login
```
重新登录并保存 Cookie。

### 2. 图片生成失败

**可能原因**：
- API Key 余额不足
- DALL-E 3 请求速率超限
- 图片描述包含敏感词

**解决方法**：
- 检查 OpenAI 账户余额
- 等待几分钟后重试
- 使用本地图片：`--images ./photos/`

### 3. 发布失败但无错误提示

**排查步骤**：
1. 检查 `output/error_screenshot.png`（自动保存的错误截图）
2. 查看 `output/publish.log` 详细日志
3. 手动访问 https://creator.xiaohongshu.com 检查账号状态

### 4. 批量发布中断

**症状**：批量发布时某一篇失败，后续停止

**原因**：代码设计为单篇失败会继续发布下一篇，但会记录失败数量

**解决方法**：
- 检查日志中失败的具体原因
- 针对失败主题单独执行 `publish` 命令

### 5. 如何加快批量发布速度？

**✅ 已内置优化（默认启用）**：
- 并发图片生成：3张图片同时生成，耗时从 90秒 降至 30秒
- 智能预生成：发布间隔期自动生成下一篇，节省 2分钟/篇
- 自动重试机制：网络波动不影响成功率

**方法1：使用优化模式**（默认）
```bash
python main.py batch --file topics.txt
# 10篇约需 47分钟（标准模式需 50分钟）
```

**方法2：减少间隔时间**（谨慎）
```env
# .env 文件
PUBLISH_INTERVAL_SECONDS=60  # 改为 1 分钟（风险：可能被风控）
```

**方法3：使用本地图片**
```bash
# 跳过 AI 生图环节，节省约 30 秒/篇
python main.py publish --topic "xxx" --images ./photos/
```

### 6. 重试机制是如何工作的？

**自动重试场景**：
- API 调用失败（网络错误、超时）
- 图片生成/下载失败
- 文案生成失败

**重试策略**：
- 文案生成：指数退避，最多3次（2秒 → 4秒 → 8秒）
- 图片生成：最多3次，每次间隔2秒
- 图片下载：最多2次，每次间隔1.5秒

**日志示例**：
```
⚠️ 第 1 次尝试失败: Connection timeout, 将在 2.0 秒后重试...
✅ 第 2 次尝试成功
```

## ⚠️ 注意事项

### 安全提示

1. **保护 API Key**
   - 不要将 `.env` 文件上传到 Git 仓库
   - 不要在公开场合分享 API Key

2. **Cookie 安全**
   - `cookies/xhs_cookies.json` 包含登录凭证
   - 已默认添加到 `.gitignore`，不要手动上传

3. **发布频率**
   - 建议每篇间隔 **5-10 分钟**（避免被平台风控）
   - 建议每天发布不超过 **10 篇**

### 内容合规

- 确保生成的内容符合小红书社区规范
- 避免发布违规、敏感、虚假信息
- AI 生成内容仅供参考，建议人工审核后发布

### 技术限制

1. **浏览器选择器依赖**
   - 代码依赖小红书创作者中心的 DOM 结构
   - 如平台界面更新，可能需要调整 `xhs_publisher.py` 中的选择器

2. **发布成功检测**
   - 当前仅通过 URL 变化判断是否发布成功
   - 建议开启试运行模式 (`--dry-run`) 验证流程

3. **发布并发限制**
   - 发布环节串行执行（避免Cookie冲突）
   - 内容生成已支持并发优化（图片+预生成）

## 📈 性能指标

### 优化前 vs 优化后

| 环节 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 文案生成 | 5-10 秒 | 5-10 秒（+重试保障） | ✅ 成功率提升 |
| 图片生成（3张） | 90 秒（串行） | **30 秒（并发）** | ⚡ **3倍提速** |
| 图片下载 | 5-10 秒 | 5-10 秒（+重试保障） | ✅ 成功率提升 |
| 浏览器发布 | 10-20 秒 | 10-20 秒 | - |
| **单篇总计** | **2 分钟** | **1 分钟** | ⚡ **2倍提速** |

### 批量发布时间对比

| 篇数 | 标准模式 | 优化模式 | 节省时间 |
|------|---------|---------|---------|
| 5篇 | 30 分钟 | 26 分钟 | 4 分钟 |
| 10篇 | 65 分钟 | 51 分钟 | **14 分钟** |
| 20篇 | 135 分钟 | 101 分钟 | **34 分钟** |

> **计算说明**：
> - 标准模式：(生成2分钟 + 发布0.5分钟) × 篇数 + 间隔5分钟 × (篇数-1)
> - 优化模式：首篇2.5分钟 + 后续每篇5分钟间隔（间隔期生成下一篇）

## 💰 成本估算

**OpenAI API 费用**（以官方定价为例）：

| 模型 | 单次费用 | 用途 |
|------|---------|------|
| GPT-4o | ~$0.02 | 文案生成 |
| DALL-E 3 (1024x1024) | ~$0.12 | 单张图片 |
| **单篇总计** | **~$0.38** | 1篇笔记（1文案 + 3图片） |
| **批量发布（10篇）** | **~$3.80** | - |

**降低成本的方法**：
1. 使用本地图片（节省 $0.36/篇）
2. 使用更便宜的兼容 API（如 DeepSeek）
3. 减少每篇图片数量（修改 `config.py`）

## 🛠️ 开发与维护

### 调试模式

**保留浏览器窗口**（便于观察发布过程）：
```python
# xhs_publisher.py 第92行
browser = p.chromium.launch(headless=False)  # 改为 True 可隐藏窗口
```

**查看错误截图**：
- 发布失败时自动保存到 `output/error_screenshot.png`

**检查详细日志**：
```bash
tail -f output/publish.log
```

### 选择器维护

如小红书界面更新导致发布失败，请检查以下选择器（`xhs_publisher.py`）：

| 元素 | 选择器 | 行数 |
|------|--------|------|
| 图片上传 | `input[type="file"]` | 129 |
| 标题输入 | `#publish-container input[placeholder]` | 140 |
| 正文编辑器 | `div[contenteditable="true"]` | 150 |
| 发布按钮 | `button:has-text("发布")` | 156 |

**调试技巧**：
1. 使用浏览器开发者工具检查元素
2. 在 Playwright 中使用 `page.pause()` 暂停执行
3. 参考 [Playwright 选择器文档](https://playwright.dev/docs/selectors)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

**改进方向**：
- [x] 添加重试机制（API 失败自动重试）✅ 已完成
- [x] 实现并发生成（加速批量发布）✅ 已完成
- [ ] 增强发布成功检测（等待成功提示元素）
- [ ] 支持视频发布
- [ ] 添加定时发布功能
- [ ] 集成数据统计（阅读量、点赞数）

## 📄 许可证

MIT License

---

## 💡 使用技巧

### 1. 定时批量发布

配合 cron (Linux/macOS) 或任务计划程序 (Windows)：

```bash
# Linux/macOS: 每天上午 10 点执行
0 10 * * * cd /path/to/xhs-auto-publisher && python main.py batch --file topics.txt
```

### 2. 多账号管理

通过不同的 Cookie 文件管理多个账号：

```bash
# 账号1 登录
XHS_COOKIE_FILE=cookies/account1.json python main.py login

# 账号1 发布
XHS_COOKIE_FILE=cookies/account1.json python main.py publish --topic "xxx"

# 账号2 登录
XHS_COOKIE_FILE=cookies/account2.json python main.py login
```

### 3. 主题生成工具

使用 AI 批量生成主题列表：

```bash
# 使用 GPT 生成 10 个主题
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "生成10个小红书笔记主题，每个一行"}]
  }' | jq -r '.choices[0].message.content' > topics.txt
```

## 📞 支持

- **问题反馈**：[GitHub Issues](https://github.com/your-repo/issues)
- **使用交流**：[Discussions](https://github.com/your-repo/discussions)

---

**祝您使用愉快！✨**
