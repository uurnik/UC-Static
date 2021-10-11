# Development container for frontend
FROM node:latest

WORKDIR /app

COPY package*.json ./
COPY . .

RUN npm install

CMD ["npm", "run", "serve", "--" ,"--port","3000"]