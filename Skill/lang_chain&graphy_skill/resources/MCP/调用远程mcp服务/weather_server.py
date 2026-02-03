# https://docs.langchain.com/oss/python/langchain/mcp#custom-mcp-servers

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("weather")  # weather 为服务名


@mcp.tool()
async def get_weathe_1(location: str) -> str:
    """Get weather for n纽约."""
    return "It's always sunny in New York"


@mcp.tool()
async def get_weathe_2(location: str) -> str:
    """Get weather for 北京."""
    return "北京台风"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
    