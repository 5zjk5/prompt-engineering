---
name: byteplus-edge-pages-deploy
description: "Deploy static websites to BytePlus Edge Pages with CDN. Invoke when user asks to deploy/publish/host a static site, or mentions BytePlus/Edge Pages/CDN deployment."
---

# BytePlus Edge Pages 部署技能

## 概述

将静态网站一键部署到 BytePlus Edge Pages 平台，获得 CDN 加速。纯 Node.js 实现，零外部依赖，Windows/Mac/Linux 均可运行。

**本技能经过实际踩坑修复，解决了两个导致部署后页面 404 的致命 Bug。请务必阅读"踩坑记录"章节。**

---

## 触发条件

- 用户要求"部署"/"发布"/"上线"静态网站
- 用户提到 "BytePlus"/"Edge Pages"/"CDN 部署"
- 用户要求重新部署或更新已有项目

---

## 场景检测

技能调用时，先判断用户属于哪个场景：

1. 检查 `scripts/config.json` 是否存在且已配置真实凭证（非 `YOUR_` 开头的占位符）
2. 已配置 → **场景A**（直接部署）
3. 未配置 → 询问用户是否有 BytePlus 账号
   - 有 → 引导获取 AK/SK（场景A 前提条件）
   - 无 → **场景B**（完整引导流程）

---

## 场景A：直接部署（已有账号和凭证）

### 前提条件

1. `scripts/config.json` 已配置 BytePlus AK/SK
   - 首次使用：复制 `scripts/config.template.json` 为 `config.json`，填入凭证
   - 获取地址：https://console.byteplus.com/iam/keymanage
2. 静态网站目录包含 `index.html`
3. Node.js 已安装（零外部依赖）

### 部署

```bash
node scripts/deploy.js --dir <网站目录> [--name <项目名>] [--project-id <已有项目ID>]
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--dir` | 是 | 静态网站目录（须含 index.html） |
| `--name` | 否 | 项目名（默认取目录名） |
| `--project-id` | 否 | 已有项目 ID（提供后直接更新，跳过查找） |

**部署逻辑（已修复，详见踩坑记录 #2）：**
- 有 `--project-id` → 直接上传内容并调用 `CreatePagesDeployment` 创建新部署
- 有 `--name` → 按名查找；找到则上传内容并创建新部署；找不到则创建项目
- **新建项目时会自动执行二次部署**：第一次是 `CreatePagesProject` 产生的初始部署（内容无法正常访问，返回 404），第二次是 `CreatePagesDeployment` 产生的正式部署（可正常访问）

### 检查部署状态

```bash
node scripts/check_status.js --project-id <项目ID>
```

每 15 秒轮询（最多 10 次），状态 `online` 后输出预览链接，并自动 HTTP 验证链接是否返回 200（检测 404 问题）。

### 项目管理

```bash
# 列出所有项目（查看已有项目 ID）
node scripts/manage.js list

# 查看项目详情
node scripts/manage.js get --project-id <项目ID>

# 查看部署历史
node scripts/manage.js deployments --project-id <项目ID>

# 下线项目
node scripts/manage.js offline --project-id <项目ID>

# 删除项目（释放项目配额）
node scripts/manage.js delete --project-id <项目ID>
```

### 测试

部署完成后，脚本会自动验证预览链接的 HTTP 状态码。也可以用浏览器手动打开预览链接验证。

---

## 场景B：新用户引导（没有 BytePlus 账号）

多步对话流程，每步等待用户确认后继续。

### 步骤1：注册账号

> 部署需要一个 BytePlus 账号。我来打开注册页面。
>
> 完成以下步骤：
> 1. 注册 BytePlus 账号
> 2. 完成个人身份验证
> 3. 添加信用卡用于计费
>
> 完成后回来告诉我。

```bash
node scripts/onboard.js open-browser "https://signin.byteplus.com/auth/signup"
```

### 步骤2：获取 AK/SK

> 现在需要创建 Access Key 用于 API 访问。
>
> 在 IAM 页面：
> 1. 点击"Create Access Key"
> 2. 复制 Access Key ID 和 Secret Access Key
>
> 格式示例：
> - Access Key ID: `AKLTMjY2MD...`
> - Secret Access Key: `T1dHVn...`
>
> 获取后粘贴给我。

```bash
node scripts/onboard.js open-browser "https://console.byteplus.com/iam/keymanage"
```

### 步骤3：保存凭证

用户提供 AK/SK 后：

```bash
node scripts/onboard.js save-credentials "<access_key>" "<secret_key>"
```

### 步骤4：开通 CDN 服务

> 需要开通 BytePlus CDN 服务以启用 Edge Pages。
> - 服务：BytePlus CDN（按量计费）
> - 区域：海外加速
>
> 是否继续开通？

用户确认后：

```bash
node scripts/onboard.js subscribe-cdn
```

### 步骤5：部署

引导完成，进入正常部署流程（同场景A）。

---

## 完整流程

### 新用户（场景B）
```
步骤1: 注册 BytePlus 账号 → onboard.js open-browser
步骤2: 获取 AK/SK → onboard.js open-browser
步骤3: 保存凭证 → onboard.js save-credentials
步骤4: 开通 CDN → onboard.js subscribe-cdn
步骤5: 部署 → deploy.js --dir ./my-site --name my-project
步骤6: 获取链接 → check_status.js --project-id p-xxx
步骤7: 浏览器测试
```

### 老用户（场景A）
```
步骤1: 部署 → deploy.js --dir ./my-site --name my-project
步骤2: 获取链接 → check_status.js --project-id p-xxx
步骤3: 浏览器测试
步骤4: 迭代更新 → deploy.js --dir ./my-site --name my-project
```

---

## 文件结构

```
scripts/
├── config.template.json  # 凭证模板（复制为 config.json 后填入 AK/SK）
├── config.json           # 凭证配置（用户私有，含 AK/SK）
├── lib.js                # 公共库（API签名、HTTP、上传、跨平台ZIP打包）★ 含关键修复
├── deploy.js             # 部署脚本（创建/更新项目）★ 含关键修复
├── check_status.js       # 状态轮询 + HTTP 验证（获取预览链接，检测 404）
├── manage.js             # 项目管理（list/get/deployments/offline/delete）
└── onboard.js            # 新用户引导（注册/获取凭证/开通CDN）
```

---

## 踩坑记录（必读）

本技能在实际使用中遇到了多个致命问题，以下为详细记录和修复方案。**这些问题已在当前脚本中全部修复，但如果重新生成或修改脚本，务必注意以下几点。**

### 坑 #1：Windows Compress-Archive 生成的 ZIP 导致 404

**现象：** 在 Windows 上部署成功（API 返回成功），但访问预览链接返回 404 Not Found。

**根因：** Windows PowerShell 的 `Compress-Archive` 命令生成的 ZIP 文件格式与 BytePlus Edge Pages 的解压服务不兼容。虽然 ZIP 文件本身是合法的，但 BytePlus 服务端无法正确解析其中的文件结构，导致部署的文件未被识别，页面返回 404。

**修复（在 `lib.js` 的 `createZip()` 函数中）：**
- Windows 上优先使用 `tar -a -cf` 命令（Windows 10 1803+ 自带的 bsdtar）
- `tar` 生成的 ZIP 格式与 Linux 的 `zip` 命令兼容，BytePlus 能正确解析
- 仅当 `tar` 不可用时才降级使用 `Compress-Archive`，并输出警告

```javascript
// 修复前（有问题）：
execSync(`powershell -Command "Compress-Archive -Path '${dirPath}\\*' -DestinationPath '${tmpZip}' -Force"`);

// 修复后（正确）：
execSync(`tar -a -cf "${tmpZip}" -C "${dirPath}" .`);
```

**验证方法：** 部署后用 `check_status.js` 或 `deploy.js` 内置的 HTTP 验证检查预览链接是否返回 200。

### 坑 #2：DeployPagesProject API 不会创建新部署

**现象：** 对已有项目执行更新部署时，API 返回 `"Operation denied: deployment xxx is already in use, no need to deploy"`，页面内容不更新。

**根因：** 原版脚本使用 `DeployPagesProject` API 来部署已有项目。但该 API 的行为是：如果项目已有部署且内容未变，则返回"无需重复部署"。即使内容已变，该 API 也不会创建新的 Deployment 记录，导致页面内容无法更新。

**修复（在 `deploy.js` 中）：**
- 所有部署操作统一使用 `CreatePagesDeployment` API
- 该 API 会强制创建新的 Deployment 记录，确保内容更新生效
- `uploadAndDeploy()` 函数封装了"获取上传信息 → 上传 ZIP → 创建部署"的完整流程

```javascript
// 修复前（有问题）：
const deployRes = await api('DeployPagesProject', { ProjectID: projectId });

// 修复后（正确）：
const sourceConfig = { Type: 'upload', Directory: uploadDir, AssetsDir: uploadDir };
const deployRes = await api('CreatePagesDeployment', { ProjectID: projectId, SourceConfig: sourceConfig });
```

### 坑 #3：CreatePagesProject 的初始部署无法访问

**现象：** 新建项目后，项目状态显示 `online`，但访问预览链接返回 404。

**根因：** `CreatePagesProject` API 要求传入 `SourceConfig` 参数，这会产生一个初始部署。但这个初始部署虽然状态为 `success`，内容却无法被 CDN 正确访问（返回 404）。必须额外调用 `CreatePagesDeployment` 创建一次正式部署，页面才能正常访问。

**修复（在 `deploy.js` 中）：**
- 新建项目时，先上传内容并带 `SourceConfig` 创建项目
- 等待初始部署完成（状态变为 `online`）
- 然后再次上传内容并调用 `CreatePagesDeployment` 创建正式部署
- 这一步是必须的，不能省略

### 坑 #4：项目数量配额限制（上限 5 个）

**现象：** 创建新项目时报错 `"quota exceeded: quota project.count.limit is 5"`。

**根因：** BytePlus Edge Pages 的项目数量上限为 5 个（免费配额）。当已有 5 个项目时，无法创建新项目。

**解决方案：**
- 用 `manage.js list` 查看所有项目
- 用 `manage.js delete --project-id <ID>` 删除不需要的项目释放配额
- 或用 `--project-id` 参数直接部署到已有项目（更新而非新建）

```bash
# 查看所有项目
node scripts/manage.js list

# 删除不需要的项目
node scripts/manage.js delete --project-id p-xxxxx

# 然后重新部署
node scripts/deploy.js --dir ./my-site --name my-project
```

### 坑 #5：CDN 传播延迟

**现象：** 部署成功且 API 返回状态为 `online`，但立即访问预览链接返回 404 或旧内容。

**根因：** CDN 内容传播需要时间，通常 1-5 分钟。部署 API 返回成功并不意味着 CDN 边缘节点已同步最新内容。

**修复（在 `deploy.js` 和 `check_status.js` 中）：**
- 部署后自动循环 HTTP 验证预览链接（最多 4 次，每次间隔 15 秒）
- `check_status.js` 在输出链接后也会进行 HTTP 验证
- 如果首次访问返回 404，脚本会提示"等待 CDN 传播"

### 坑 #6：BytePlus 官方文档不稳定

**现象：** 开发过程中尝试查阅 BytePlus Edge Pages API 文档时，文档页面返回 Internal Server Error。

**影响：** 无法通过官方文档确认 API 参数格式，只能通过试错法（trial and error）逆向推导正确的 API 调用方式。

**应对：** 本技能中所有 API 调用参数均经过实际验证，可直接使用。关键 API 清单：

| API Action | 用途 | 关键参数 |
|------------|------|----------|
| `ListPagesProject` | 列出所有项目 | 无 |
| `CreatePagesProject` | 创建新项目 | `Name`, `Description`, `SourceConfig` |
| `GetPagesProject` | 获取项目详情 | `ProjectID` |
| `DeletePagesProject` | 删除项目 | `ProjectID` |
| `GetPagesDeploymentUploadInfo` | 获取上传地址 | 无 |
| `CreatePagesDeployment` | 创建新部署（核心） | `ProjectID`, `SourceConfig` |
| `ListPagesDeployment` | 列出部署历史 | `ProjectID` |
| `OfflinePagesProject` | 下线项目 | `ProjectID` |
| `SubscribeCdnService` | 开通 CDN 服务 | `Regions` |

### 坑 #7：API 网络波动需要重试

**现象：** BytePlus API 偶尔返回网络错误或超时，单次调用可能失败。

**修复（在 `lib.js` 的 `api()` 函数中）：**
- 内置自动重试机制，默认 8 次，每次间隔 5 秒
- 上传文件操作也有重试（8 次）
- 最终失败时返回包含错误信息的结构化对象，不会直接崩溃

---

## 兼容性说明

### 操作系统兼容性

| 系统 | ZIP 打包方式 | 状态 |
|------|-------------|------|
| Windows 10 1803+ | `tar -a -cf`（bsdtar 自带） | ✅ 已修复 |
| Windows 旧版本 | `Compress-Archive`（降级，可能有 404 问题） | ⚠️ 不推荐 |
| macOS | `zip -r` | ✅ 正常 |
| Linux | `zip -r` | ✅ 正常 |

### Node.js 版本

- 需要 Node.js 14+（使用了 `fs.rmSync` 等 API 的兼容写法）
- 零外部依赖，仅使用 Node.js 内置模块（`crypto`, `https`, `fs`, `path`, `child_process`, `os`）

### API 签名

- 使用 BytePlus Signature V4（HMAC-SHA256）签名算法
- 签名区域：`ap-singapore-1`
- 签名服务：`CDN`
- API 版本：`2021-03-01`
- API 主机：`cdn.byteplusapi.com`

---

## 常见问题排查

### Q: 部署成功但页面 404？

依次检查：
1. **ZIP 格式问题** → 确认 `lib.js` 中 Windows 使用 `tar` 而非 `Compress-Archive`
2. **API 调用问题** → 确认 `deploy.js` 使用 `CreatePagesDeployment` 而非 `DeployPagesProject`
3. **新建项目未二次部署** → 确认新建项目后执行了 `CreatePagesDeployment`
4. **CDN 传播延迟** → 等待 1-5 分钟后重试 `check_status.js`

### Q: 创建项目报配额超限？

用 `manage.js list` 查看项目列表，删除不需要的项目（上限 5 个）。

### Q: API 调用报签名错误？

检查 `config.json` 中的 AK/SK 是否正确，确保没有多余空格或换行。AK/SK 获取地址：https://console.byteplus.com/iam/keymanage

### Q: 上传失败？

脚本会自动重试 8 次。如果仍然失败，检查网络连接和 `config.json` 中的凭证是否有效。

---

## 已部署项目记录

| 项目名 | 项目 ID | 说明 |
|--------|---------|------|
| pomodoro-timer | p-2e9gpjd4tav9n9yf | 番茄钟计时器 |
| hello-world | （部署后填入） | Hello World 测试页 |
