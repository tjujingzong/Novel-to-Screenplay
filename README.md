# Novel to Screenplay

AI 驱动的小说转剧本工具 —— 将小说文本自动转换为结构化 YAML 剧本，降低改编门槛，提升创作效率。

## 功能特性

- **多格式输入**：支持 TXT、Markdown、DOCX、PDF 四种格式的小说文件
- **智能章节检测**：正则匹配（中/英文/罗马数字章节标题）+ 启发式分段，自动识别章节边界
- **角色目录提取**：通过 LLM 从小说文本中提取完整的角色列表，包括姓名、别名、角色定位、人物关系
- **逐章剧本转换**：采用"滑动窗口 + 记忆"策略，每章转换后生成连续性摘要传递给下一章，保证多章节间的一致性
- **结构化 YAML 输出**：生成符合行业标准的剧本 YAML 文件，包含 metadata、characters、structure（acts → scenes → elements）三层结构
- **Web 界面**：拖拽上传、实时进度条、YAML 语法高亮预览、一键下载
- **Schema 验证**：自动校验生成的剧本，检测角色引用错误、编号不连续等问题

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| 后端框架 | FastAPI (Python) |
| LLM 服务 | DeepSeek API (OpenAI 兼容接口) |
| 前端 | Jinja2 + Tailwind CSS + 原生 JS |
| YAML 生成 | ruamel.yaml |
| 文件解析 | python-docx / pdfplumber |
| 数据验证 | Pydantic v2 |
| 测试 | pytest + pytest-asyncio |
| 代码规范 | ruff |

## 快速开始

### 1. 环境要求

- Python >= 3.10
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 2. 安装

```bash
cd novel
python3 -m venv .venv
source .venv/bin/activate

在 Windows PowerShell 中，激活虚拟环境的命令是：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果是 CMD 的话：

```cmd
.venv\Scripts\activate.bat
```

# 安装所有依赖（含开发依赖）
pip install -e ".[dev]"
```

### 3. 配置

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MAX_UPLOAD_SIZE_MB=50
DATA_DIR=./data
```

### 4. 启动

```bash
python -m uvicorn app.main:app --reload --port 8000
```

浏览器访问 [http://localhost:8000](http://localhost:8000)。

## 使用流程

1. **上传文件**：在首页拖拽或点击上传小说文件（TXT / MD / DOCX / PDF）
2. **开始转换**：点击"Start Conversion"按钮
3. **等待处理**：页面实时显示转换进度（解析文件 → 检测章节 → 提取角色 → 逐章转换 → 组装 → 验证）
4. **查看结果**：转换完成后，可在线预览带语法高亮的 YAML 输出，或下载 YAML 文件

## 项目结构

```
novel/
├── pyproject.toml              # 项目配置与依赖管理
├── .env.example                # 环境变量模板
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理 (pydantic-settings)
│   ├── dependencies.py         # 共享依赖（模板引擎等）
│   ├── api/
│   │   └── routes.py           # API 路由（上传/转换/进度/下载/预览）
│   ├── models/
│   │   ├── enums.py            # 枚举类型（角色类型、时间、转场等）
│   │   ├── screenplay.py       # YAML Schema 的 Pydantic 模型定义
│   │   └── requests.py         # API 请求/响应模型
│   ├── services/
│   │   ├── file_parser.py      # 多格式文本提取
│   │   ├── chapter_splitter.py # 章节检测与切分
│   │   ├── llm_client.py       # DeepSeek API 异步客户端
│   │   ├── character_extractor.py  # LLM 角色提取
│   │   ├── converter.py        # 核心转换引擎
│   │   ├── assembler.py        # 剧本组装
│   │   ├── validator.py        # 结构验证
│   │   └── yaml_exporter.py    # YAML 导出
│   ├── prompts/                # LLM Prompt 模板
│   ├── templates/              # Jinja2 HTML 模板
│   └── static/                 # 前端 CSS / JS
├── docs/
│   └── YAML_SCHEMA.md          # YAML Schema 定义文档（含设计说明）
└── tests/                      # 55 个单元/集成测试
```

## 处理流水线

```
上传文件 → 文本提取 → 章节切分 → 角色提取 → 逐章转换 → 组装 → 验证 → YAML 导出
                │           │          │          │
              TXT/MD/    正则+启发式   LLM     LLM + 连续性上下文
              DOCX/PDF   两级检测    去重合并  滑动窗口策略
```

每次 LLM 调用的 Token 预算分配：

| 组件 | Token 预算 | 说明 |
|------|-----------|------|
| 系统 Prompt | ~800 | 角色设定 + 输出格式 |
| 角色目录 | ~500 | 压缩格式的角色列表 |
| 前章上下文 | ~200 | 2 句话摘要 |
| 章节文本 | ~5,000 | 当前章节内容 |
| 输出 JSON | ~4,000 | 生成的剧本元素 |

超长章节会在场景断点处自动子切分。

## YAML Schema 概览

生成的剧本 YAML 遵循自定义 Schema（详见 [docs/YAML_SCHEMA.md](docs/YAML_SCHEMA.md)），结构如下：

```yaml
screenplay:
  metadata:        # 标题、作者、类型、语言、版本、时间戳
  characters:      # 角色目录（id, name, role, description, relationships）
  structure:
    acts:          # 幕 → 场景 → 元素
      - scenes:
          heading:   # { location, time_of_day, int_ext }
          elements:  # action | dialogue | parenthetical | transition | note
  notes:           # 全局注释
```

设计原则：
- **可往返**：YAML → 渲染剧本 → YAML 不丢失语义
- **LLM 友好**：字段名清晰无歧义，LLM 可直接填充
- **人类可编辑**：在任意文本编辑器中打开即可修改

## 开发与测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 代码检查
ruff check app/ tests/

# 自动修复 lint 问题
ruff check app/ tests/ --fix
```

## 配置参数

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `DEEPSEEK_API_KEY` | (必填) | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 基础 URL |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 使用的模型 |
| `MAX_UPLOAD_SIZE_MB` | `50` | 最大上传文件大小 (MB) |
| `DATA_DIR` | `./data` | 运行时数据目录 |

## 部署

### Zeabur 一键部署（推荐）

项目已内置 [Dockerfile](Dockerfile)，支持 Zeabur 一键部署。Zeabur 支持支付宝/微信登录，香港节点国内访问快。

#### 步骤

1. **推送代码到 GitHub**

   ```bash
   git add Dockerfile .dockerignore
   git commit -m "chore: add Zeabur deployment config"
   git push
   ```

2. **在 Zeabur 创建服务**

   - 注册/登录 [Zeabur](https://zeabur.com)（支持 GitHub / 支付宝 / 微信登录）
   - 点击 **New Project**，选择服务器地区（推荐 **Hong Kong**）
   - 点击 **Add Service** → **Deploy from GitHub repository** → 选择本仓库

3. **配置环境变量**

   部署后在 Zeabur 控制台的 **Environment Variables** 中添加：

   | 变量名 | 值 | 说明 |
   |--------|------|------|
   | `DEEPSEEK_API_KEY` | `sk-your-key-here` | **必填**，DeepSeek API 密钥 |
   | `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 可按需修改 |
   | `DEEPSEEK_MODEL` | `deepseek-chat` | 可按需修改 |
   | `DATA_DIR` | `/data` | Docker 容器内数据路径 |

   填入后 Zeabur 会自动重新部署。

4. **访问服务**

   - 部署完成后（约 2–3 分钟），在 **Service → Domain** 中获取公网地址
   - 访问 `https://your-project.zeabur.app` 即可使用
   - 也可在 Domain 设置中绑定自定义域名

> **说明**：Zeabur 按用量计费，每月有免费额度（约 ¥5），普通使用基本不花钱。详见 [Zeabur 定价](https://zeabur.com/pricing)。

### 手动部署（自有服务器 / 云服务器）

适用于已有阿里云、腾讯云等国内云服务器的场景。

```bash
# 构建 Docker 镜像
docker build -t novel-to-screenplay .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e DEEPSEEK_API_KEY=sk-your-key-here \
  -e DATA_DIR=/data \
  -v $(pwd)/data:/data \
  --name novel-to-screenplay \
  novel-to-screenplay
```

启动后访问 `http://你的服务器IP:8000`。如需公网访问，请确保云服务器安全组已放行 8000 端口。

## License

MIT
