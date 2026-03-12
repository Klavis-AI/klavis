FROM node:18-alpine

WORKDIR /app

COPY mcp_servers/youtube_toolathlon/package*.json ./

RUN npm install

COPY mcp_servers/youtube_toolathlon/ .

RUN npm run build

EXPOSE 5000

CMD ["node", "dist/index.js"]
