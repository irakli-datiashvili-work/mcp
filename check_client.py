r"""Stage 3 check: do in code what we did by hand in the Inspector.

Run from the project folder:  .\.venv\Scripts\python.exe -I scripts\check_client.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # -I removes the current folder from the import path

from mcp_client import MCPClient


def text_of(result) -> str:
    return result.content[0].text


async def main():
    async with MCPClient(command=sys.executable, args=[str(ROOT / "mcp_server.py")]) as client:
        tools = await client.list_tools()
        print("1. tools:", [t.name for t in tools])

        result = await client.call_tool("read_doc_contents", {"doc_id": "plan.md"})
        print("2. read plan.md ->", text_of(result))

        await client.call_tool(
            "edit_document",
            {"doc_id": "plan.md", "old_str": "implementation", "new_str": "delivery"},
        )
        result = await client.call_tool("read_doc_contents", {"doc_id": "plan.md"})
        print("3. after edit   ->", text_of(result))

        result = await client.call_tool("read_doc_contents", {"doc_id": "nope.md"})
        print("4. nope.md      -> isError =", result.isError, "|", text_of(result))


asyncio.run(main())
