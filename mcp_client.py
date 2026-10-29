from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPClient:
    """Starts an MCP server as a subprocess and talks to it over stdio.

    Use it as `async with MCPClient(command=..., args=[...]) as client:` so the
    connection is always cleaned up, even if something fails in the middle.
    """

    def __init__(self, command: str, args: list[str]):
        self._params = StdioServerParameters(command=command, args=args)
        self._exit_stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def connect(self):
        # stdio_client starts the server process and gives us its read/write streams.
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self._params)
        )
        # ClientSession is the SDK object that speaks the MCP protocol on those streams.
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError("Client not connected. Use `async with MCPClient(...)`.")
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(tool_name, tool_input)

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc_info):
        await self.cleanup()
