from fastmcp import FastMCP

mcp = FastMCP("test-server")

@mcp.tool()
def ping():
    return "pong"

if __name__ == "__main__":
    print(">>> Subindo server")
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp",
    )