ARG NODE_BASE_IMAGE=docker.m.daocloud.io/library/node:20-alpine
ARG NGINX_BASE_IMAGE=docker.m.daocloud.io/library/nginx:alpine
FROM ${NODE_BASE_IMAGE} AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

FROM ${NGINX_BASE_IMAGE}

COPY --from=build /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
