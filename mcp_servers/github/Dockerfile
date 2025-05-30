FROM golang:1.23-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy go.mod and go.sum files first for better caching
COPY mcp_servers/github/go.mod mcp_servers/github/go.sum ./
RUN go mod download

# Copy the source code
COPY mcp_servers/github/ ./

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o server server.go

# Create a minimal production image
FROM alpine:3.19

WORKDIR /app

# Add ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Copy the binary from the builder stage
COPY --from=builder /app/server .

# Expose the default port
EXPOSE 5000

# Run the server
CMD ["./server"] 