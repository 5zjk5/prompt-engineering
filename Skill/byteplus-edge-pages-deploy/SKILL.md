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
- 用户要求"绑定域名"/"自定义域名"/"配置域名"
- 用户提到默认域名失效/过期/不能访问

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

### 部署前必须确认：部署到哪个项目？

由于自定义域名配额只有 1 个，部署前**必须询问用户**：

> 这个网站是要发布到主站（永久访问），还是临时预览？
>
> - **主站**（app.muxiatong.top）→ 部署到 web-app-01（`--project-id p-2e9j5dbfm9ziu5uu`），内容会替换主站当前内容
> - **临时预览**（3小时有效）→ 部署到 web-app-02~05 中的任意一个，获得临时预览链接
> - **新项目** → 如果 5 个项目都已占满且都不想覆盖，需先删除一个再创建

根据用户选择使用对应的项目 ID：

| 用途 | 项目名 | 项目 ID | 域名 |
|------|--------|---------|------|
| 主站（永久） | web-app-01 | p-2e9j5dbfm9ziu5uu | app.muxiatong.top |
| 临时预览1 | web-app-02 | p-2e9iyp4817qtuepq | 默认预览域名 |
| 临时预览2 | web-app-03 | p-2e9k954c31x9l5sm | 默认预览域名 |
| 临时预览3 | web-app-04 | p-2e9gy188chzot8ti | 默认预览域名 |
| 临时预览4 | web-app-05 | p-2e9h1540alc7nkl2 | 默认预览域名 |

**重要：** 用 `--project-id` 部署到已有项目时，旧内容会被新内容替换，项目 ID 和域名绑定不变。不需要删除重建。

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

## 自定义域名管理

### 默认域名 vs 自定义域名

部署成功后，BytePlus 会自动分配一个预览域名，格式为 `p-xxx.synthopages.bytepluses.com`。

**重要：默认预览域名每 3 小时重置一次，不能作为稳定访问地址！** 必须绑定自定义域名才能长期使用。

| 类型 | 域名格式 | 稳定性 | SSL |
|------|---------|--------|-----|
| 默认预览域名 | `p-xxx.synthopages.bytepluses.com?_token=...` | 每 3 小时失效 | 无 |
| 自定义域名 | `app.yourdomain.com` | 永久有效 | 自动配置 |

### 部署后流程

```
部署成功 → 获得默认预览域名（3小时有效）
    ↓
用户有自有域名？
    ├─ 是 → 绑定自定义域名（见下方）
    └─ 否 → 告知用户默认域名 3 小时后失效，建议尽快绑定自有域名
```

### 一键绑定域名

```bash
node scripts/domain.js bind --project-id <项目ID> --domain <你的域名>
```

此命令会自动完成：
1. 调用 `AddPagesDomain` API 添加域名
2. 轮询 `GetPagesDomain` 等待 CNAME 地址生成
3. 输出 DNS 配置指引（记录类型、主机记录、记录值）
4. 提示用户去域名 DNS 管理处添加 CNAME 记录
5. 提示用户配置完成后运行 verify 验证

### 绑定域名的交互流程（AI 必须遵守）

绑定域名涉及用户手动操作 DNS，AI 不能只跑命令就结束，**必须按以下步骤引导用户**：

**步骤1：AI 运行 bind 命令，拿到 CNAME 地址**

```bash
node scripts/domain.js bind --project-id <项目ID> --domain <域名>
```

**步骤2：AI 主动告诉用户去 DNS 管理处配置**

拿到 CNAME 地址后，AI 必须向用户输出清晰的配置指引，例如：

> 域名已添加成功！CNAME 地址是 `app.muxiatong.top.bplslb.com`。
>
> 现在需要你去阿里云域名控制台添加一条 CNAME 记录：
>
> | 项目 | 填什么 |
> |------|--------|
> | 记录类型 | CNAME |
> | 主机记录 | app |
> | 记录值 | app.muxiatong.top.bplslb.com |
> | TTL | 默认 |
>
> 操作路径：阿里云控制台 → 域名 → muxiatong.top → 解析 → 添加记录
>
> 如果主机记录已存在其他记录（如 A 记录），需要先删除或修改，否则会报"解析冲突"。
>
> 配置完成后告诉我，我来帮你验证。

**步骤3：等用户确认配置完成**

AI 必须等待用户回复"配好了"之类确认后，才能进行验证。不要跳过这一步。

**步骤4：AI 运行 verify 验证**

```bash
node scripts/domain.js verify --project-id <项目ID> --domain <域名>
```

**步骤5：告知用户访问方式和注意事项**

验证通过后，AI 必须告知用户：
- HTTP 可立即访问，HTTPS 可能需要 5-15 分钟（SSL 证书配置中）
- 如遇 421 Misdirected Request 是 CDN 传播中，等待即可
- 自定义域名永久有效，不像默认预览域名那样 3 小时失效

### 手动分步操作

```bash
# 1. 添加域名
node scripts/domain.js add --project-id <项目ID> --domain app.example.com

# 2. 查看域名详情（获取 CNAME 地址）
node scripts/domain.js get --project-id <项目ID> --domain app.example.com

# 3. 列出项目所有域名
node scripts/domain.js list --project-id <项目ID>

# 4. DNS 配置完成后验证
node scripts/domain.js verify --project-id <项目ID> --domain app.example.com

# 5. 删除域名
node scripts/domain.js delete --project-id <项目ID> --domain app.example.com
```

### DNS 配置方法（以阿里云为例）

获取到 CNAME 地址后，在域名 DNS 管理处添加一条 CNAME 记录：

| 项目 | 填什么 |
|------|--------|
| 记录类型 | CNAME |
| 主机记录 | 子域名前缀（如 `app`、`blog`、`timer`） |
| 记录值 | BytePlus 给的 CNAME 地址（如 `app.example.com.bplslb.com`） |
| TTL | 默认（600 秒） |

**注意事项：**
- 如果该主机记录已存在 A 记录等其他记录，必须先删除或修改，否则会报"解析冲突"
- **域名配额只有 1 个**：整个 BytePlus 账户只能绑定 1 个自定义域名，请选择最常用的项目绑定
- 配置 CNAME 后需等待 DNS 传播（通常几分钟）
- 如需更换绑定的项目，先删除旧域名绑定再绑新项目（CNAME 地址可能变化，需更新 DNS 记录）

### 绑定后的访问说明

| 阶段 | HTTP | HTTPS | 说明 |
|------|------|-------|------|
| DNS 刚配置 | 可能 404 | 失败 | DNS 传播中 |
| DNS 已生效 | 200 可访问 | TLS 失败 | SSL 证书配置中 |
| 完全就绪 | 200 | 200 | 正常，HTTP 和 HTTPS 均可 |

- SSL 证书由 BytePlus 自动配置，通常需要 5-15 分钟
- 在 HTTPS 就绪前，HTTP 可先使用
- 如遇 `421 Misdirected Request`，是 CDN 边缘节点传播中，等待即可

### 域名管理 API 清单

| API Action | 用途 | 关键参数 |
|------------|------|----------|
| `AddPagesDomain` | 添加自定义域名 | `ProjectID`, `Domain` |
| `GetPagesDomain` | 查看域名详情（含 CNAME 地址） | `ProjectID`, `Domain` |
| `ListPagesDomain` | 列出项目所有域名 | `ProjectID` |
| `VerifyPagesDomain` | 验证域名 DNS 配置 | `ProjectID`, `Domain` |
| `DeletePagesDomain` | 删除域名 | `ProjectID`, `Domain` |

### 多项目域名绑定

BytePlus Edge Pages 项目上限为 5 个（实测可创建 10 个），但**自定义域名配额为每账户 1 个**。这意味着只能给 1 个项目绑定自定义域名，其他项目只能用默认预览域名（3 小时失效）。

| 项目 | 域名 | 稳定性 |
|------|------|--------|
| 主项目 | `app.yourdomain.top`（自定义域名） | 永久有效 |
| 其他项目 | 默认预览域名 | 每 3 小时失效 |

**建议策略：** 把最常用的项目绑定为自定义域名作为主站，其他项目按需用默认预览域名临时预览。如需多个自定义域名，可在 BytePlus 控制台提交工单申请提升配额。

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
步骤7: 绑定域名（推荐）→ domain.js bind --project-id p-xxx --domain app.example.com
步骤8: DNS 配置（在域名管理处添加 CNAME 记录）
步骤9: 验证域名 → domain.js verify --project-id p-xxx --domain app.example.com
步骤10: 浏览器访问自定义域名
```

### 老用户（场景A）
```
步骤1: 部署 → deploy.js --dir ./my-site --name my-project
步骤2: 获取链接 → check_status.js --project-id p-xxx
步骤3: 绑定域名（推荐）→ domain.js bind --project-id p-xxx --domain app.example.com
步骤4: DNS 配置（在域名管理处添加 CNAME 记录）
步骤5: 验证域名 → domain.js verify --project-id p-xxx --domain app.example.com
步骤6: 浏览器访问自定义域名
步骤7: 迭代更新 → deploy.js --dir ./my-site --name my-project（自定义域名不变）
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
├── domain.js             # 域名管理（add/get/list/verify/delete/bind）★ 新增
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
| `AddPagesDomain` | 添加自定义域名 | `ProjectID`, `Domain` |
| `GetPagesDomain` | 查看域名详情（含 CNAME） | `ProjectID`, `Domain` |
| `ListPagesDomain` | 列出项目所有域名 | `ProjectID` |
| `VerifyPagesDomain` | 验证域名 DNS | `ProjectID`, `Domain` |
| `DeletePagesDomain` | 删除域名 | `ProjectID`, `Domain` |

### 坑 #7：API 网络波动需要重试

**现象：** BytePlus API 偶尔返回网络错误或超时，单次调用可能失败。

**修复（在 `lib.js` 的 `api()` 函数中）：**
- 内置自动重试机制，默认 8 次，每次间隔 5 秒
- 上传文件操作也有重试（8 次）
- 最终失败时返回包含错误信息的结构化对象，不会直接崩溃

### 坑 #8：默认预览域名每 3 小时失效

**现象：** 部署成功后获得的预览域名 `p-xxx.synthopages.bytepluses.com` 在几小时后无法访问。

**根因：** BytePlus 默认预览域名每 3 小时重置一次 token，这是官方设计行为，不是 Bug。

**解决：** 必须绑定自定义域名才能获得稳定的访问地址。使用 `domain.js bind` 一键绑定。

### 坑 #9：DNS 解析冲突导致无法添加 CNAME

**现象：** 在阿里云等 DNS 管理处添加 CNAME 记录时，提示"解析冲突"。

**根因：** 同一个主机记录（如 `www`）已存在 A 记录等其他类型的 DNS 记录。DNS 协议不允许同一主机记录同时存在 CNAME 和其他记录。

**解决：** 先删除该主机记录下的其他记录（特别是 A 记录），再添加 CNAME 记录。或者使用一个新的子域名（如 `app`、`blog`）避免冲突。

### 坑 #10：域名绑定后 HTTPS 无法访问

**现象：** 域名验证通过，HTTP 可访问，但 HTTPS 报 TLS 错误或 `421 Misdirected Request`。

**根因：** SSL 证书配置需要时间，CDN 边缘节点传播也需要时间。

**解决：**
- 这是正常传播过程，HTTP 先可用，HTTPS 会在 5-15 分钟后自动就绪
- `421 Misdirected Request` 是 CDN 边缘节点尚未配置完域名路由
- 无需任何操作，等待即可

### 坑 #11：自定义域名配额只有 1 个

**现象：** 给第二个项目绑定自定义域名时，API 返回 `"quota exceeded: quota domain.count.limit is 1"`。

**根因：** BytePlus Edge Pages 的自定义域名配额是**每账户 1 个**，不是每项目 1 个。即使有 5 个项目，也只能给其中 1 个绑定自定义域名。

**解决：**
- 只给最常用的主项目绑定自定义域名
- 其他项目使用默认预览域名（3 小时失效，需重新部署刷新）
- 如需多个自定义域名，在 BytePlus 控制台提交工单申请提升配额
- 或将其他项目部署到 Cloudflare Pages（免费、无限自定义域名）

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

### Q: 默认预览域名访问不了？

默认预览域名每 3 小时重置 token，过期后无法访问。这是正常行为，需要绑定自定义域名获得稳定地址：

```bash
node scripts/domain.js bind --project-id <项目ID> --domain <你的域名>
```

### Q: 添加 CNAME 记录时提示"解析冲突"？

该子域名已存在其他类型的 DNS 记录（如 A 记录）。先删除原有记录，或换一个新子域名。

### Q: 域名绑定后 HTTPS 访问报错？

SSL 证书配置需要 5-15 分钟。期间 HTTP 可先使用，HTTPS 会自动就绪。如遇 `421 Misdirected Request` 是 CDN 传播中，等待即可。

### Q: 能用通配符域名 `*.example.com` 吗？

不能。每个 BytePlus 项目的 CNAME 地址不同，必须为每个项目单独添加子域名 CNAME 记录。

### Q: 一个域名能绑定多个项目吗？

不能。BytePlus 账户自定义域名配额只有 1 个，只能绑到 1 个项目。如需多个域名，提交工单申请提升配额。

### Q: 项目配额和域名配额分别是多少？

项目配额 5 个（实测可创建 10 个），自定义域名配额 1 个（每账户）。项目可以删除重建释放配额，域名删除后也可重新绑定到其他项目。

---

## 已部署项目记录

| 项目名 | 项目 ID | 说明 | 自定义域名 |
|--------|---------|------|-----------|
| web-app-01 | p-2e9j5dbfm9ziu5uu | 主项目（自定义域名） | app.muxiatong.top |
| web-app-02 | p-2e9iyp4817qtuepq | 备用项目1 | 默认预览域名 |
| web-app-03 | p-2e9k954c31x9l5sm | 备用项目2 | 默认预览域名 |
| web-app-04 | p-2e9gy188chzot8ti | 备用项目3 | 默认预览域名 |
| web-app-05 | p-2e9h1540alc7nkl2 | 备用项目4 | 默认预览域名 |
