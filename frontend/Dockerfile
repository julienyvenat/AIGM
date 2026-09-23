# AIGM frontend -- React/Vite SPA, built to static assets and served by nginx.
#
# Vite bakes VITE_* env vars into the JS bundle at *build* time (see
# import.meta.env.VITE_API_URL / VITE_WS_URL usage across src/), so they
# must be passed as Docker build args, not runtime env vars -- see the
# `build.args` in docker-compose.prod.yml.
FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_URL
ARG VITE_WS_URL
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

RUN npm run build

FROM nginx:alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
