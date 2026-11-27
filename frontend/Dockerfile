# Multi-stage Dockerfile for building the React/Vite frontend and serving it with Nginx.

# Stage 1: Build static frontend assets with Node 20
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Bake the backend API URL into the Vite production bundle at build time
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Serve built static files via lightweight Nginx container
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
