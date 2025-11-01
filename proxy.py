from fastmcp import FastMCP

# Initialize a proxy connection to the remote FastMCP Cloud server
# The default protocol is Streamable HTTP, accessible via the /mcp endpoint.

mcp = FastMCP.as_proxy(
    backend="https://Python-AI-Hindi-Academy.fastmcp.app/mcp",
    name="Demo Remote Proxy Server"
)

def main():
    """Run the MCP proxy via STDIO (compatible with Claude Desktop)."""
    mcp.run()

if __name__ == "__main__":
    main()
