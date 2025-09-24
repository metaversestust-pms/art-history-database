# 使用官方Node.js運行時作為基礎映像
FROM node:22-alpine

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴 (Playwright需要)
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# 設置Playwright使用系統安裝的Chromium
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin/chromium-browser
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 複製package.json和package-lock.json
COPY package*.json ./

# 安裝Node.js依賴
RUN npm ci --only=production && npm cache clean --force

# 複製應用程式源碼
COPY . .

# 建立必要的目錄並設置權限
RUN mkdir -p logs data/raw data/processed models && \
    chown -R node:node /app

# 切換到非root用戶
USER node

# 暴露端口
EXPOSE 3000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node healthcheck.js || exit 1

# 啟動命令
CMD ["npm", "start"]