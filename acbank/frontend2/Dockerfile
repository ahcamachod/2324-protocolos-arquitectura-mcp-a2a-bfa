FROM node:20-alpine

WORKDIR /app

# Variables para garantizar hot reload
ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]