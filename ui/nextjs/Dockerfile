# Stage 1: Build Stage
FROM node:18-alpine AS builder
WORKDIR /app

# Install pnpm for more robust build/install
RUN npm install -g pnpm

# Copy only package.json (ไม่ต้องอ้าง path ui/nextjs/)
COPY package.json ./

# ถ้ามี pnpm-lock.yaml อยู่จริง จะก็อปเองทีหลังก็ได้
# (ถ้าจะใช้ lock ให้เพิ่ม COPY pnpm-lock.yaml ./ แล้วแน่ใจว่ามีไฟล์)

RUN pnpm install

# Copy source code and build
COPY . .
RUN pnpm run build

# Stage 2: Production Stage
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

# Install only necessary packages for running the app
RUN npm install -g pnpm

COPY --from=builder /app/package.json .
COPY --from=builder /app/node_modules .
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Health check
# (ถ้ายังไม่มี curl เช่นกัน อาจต้อง RUN apk add --no-cache curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start application
CMD ["pnpm", "start"]
