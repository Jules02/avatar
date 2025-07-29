from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("workforce")

@mcp.tool()
async def get_sth(limit: int, state: str) -> str:
    pass


if __name__ == "__main__":
    available_tools = [get_sth]

    mcp.run(transport='stdio')
