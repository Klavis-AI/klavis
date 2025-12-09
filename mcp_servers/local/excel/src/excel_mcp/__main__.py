import typer

from .server import run_sse, run_stdio, run_streamable_http

app = typer.Typer(help="Excel MCP Server")

@app.command()
def sse():
    """Start Excel MCP Server in SSE mode"""
    try:
        run_sse()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Service stopped.")

@app.command()
def streamable_http():
    """Start Excel MCP Server in streamable HTTP mode"""
    try:
        run_streamable_http()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Service stopped.")

@app.command()
def stdio():
    """Start Excel MCP Server in stdio mode"""
    try:
        run_stdio()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Service stopped.")

if __name__ == "__main__":
    app() 