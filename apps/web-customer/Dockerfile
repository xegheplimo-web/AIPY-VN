# Multi-stage build for web-customer
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate

# Copy workspace files first for better layer caching
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web-customer/package.json apps/web-customer/
COPY packages/*/package.json packages/*/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY . .
RUN pnpm --filter web-customer run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/apps/web-customer/dist /usr/share/nginx/html
COPY apps/web-customer/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
