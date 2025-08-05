from mcp import Server

server = Server.from_yaml("tools.yaml")

if __name__ == "__main__":
    server.serve()
