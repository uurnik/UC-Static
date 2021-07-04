FROM node:16-alpine3.11 as build


WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
COPY ./frontend/package.json /app/package.json
RUN npm install --silent
RUN npm install dotenv
COPY ./frontend/ /app
RUN npm run build


FROM nginx:1.21.0-alpine

RUN apk add python3 python3-dev py3-pip gcc musl-dev libffi-dev openssl-dev cargo
RUN pip3 install certbot-nginx

COPY --from=build /app/dist /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx/nginx.conf /etc/nginx/conf.d
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]