# 部署指南

## Zeabur 一键部署（推荐）

项目已内置 [Dockerfile](../Dockerfile)，支持 Zeabur 一键部署。Zeabur 支持支付宝/微信登录，香港节点国内访问快。

### 步骤

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

## 手动部署（自有服务器 / 云服务器）

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
