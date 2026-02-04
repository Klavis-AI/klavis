FROM node:24-alpine
ARG VERSION=latest
RUN addgroup -S mcp && adduser -S mcp -G mcp
RUN npm install -g mongodb-mcp-server@${VERSION}
USER mcp
WORKDIR /home/mcp
ENV MDB_MCP_LOGGERS=stderr,mcp
ENTRYPOINT ["mongodb-mcp-server"]
LABEL maintainer="MongoDB Inc <info@mongodb.com>"
LABEL description="MongoDB MCP Server"
LABEL version=${VERSION}
LABEL io.modelcontextprotocol.server.name="io.github.mongodb-js/mongodb-mcp-server"
