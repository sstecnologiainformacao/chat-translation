# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY services/frontend/package.json services/frontend/package.json

RUN pnpm install --filter frontend --frozen-lockfile

COPY services/frontend services/frontend

WORKDIR /app/services/frontend

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build

FROM nginx:1.27-alpine AS runtime

COPY --from=builder /app/services/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
