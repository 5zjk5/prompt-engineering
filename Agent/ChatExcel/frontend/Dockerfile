# ── 前端镜像：多阶段构建（node 编译 + nginx 提供静态文件）──────

# 第一阶段：用 node 编译生产包
FROM node:20-alpine AS builder
WORKDIR /app

# 先拷贝依赖清单，利用分层缓存
COPY package.json package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com && npm ci

# 拷贝源码并构建，产物输出到 dist/
COPY . .
RUN npm run build


# 第二阶段：用 nginx 提供静态文件服务
FROM nginx:alpine

# 时区设置
ENV TZ=Asia/Shanghai

# 用自定义 nginx 配置替换默认配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 拷贝构建产物到 nginx 静态目录
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
