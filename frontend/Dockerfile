# ============================================
# Frontend React/Vite — build lalu serve via Nginx (#37)
# ============================================
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# VITE_* di-inject saat build (build-time env)
ARG VITE_API_BASE_URL
ARG VITE_UPLOADS_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
