FROM node:18-alpine

WORKDIR /app

# Copy package files (จาก context ./apps/bridge)
COPY package*.json ./

# ติดตั้ง dependencies แบบ production โดยไม่ใช้ npm ci (เพราะไม่มี package-lock)
RUN npm install --only=production

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8787

# ให้มี curl สำหรับ healthcheck
RUN apk add --no-cache curl

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8787/health || exit 1

# Run worker
CMD ["npm", "start"]
