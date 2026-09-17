"""MCP 调用示例 - 纯粹演示如何通过 MCP 协议调用服务器上的工具

不涉及 LLM，只演示 MCP 客户端的标准流程:
    启动 stdio 服务器子进程 -> 建立会话 -> 列出工具 -> 调用工具

运行方式:
    python tools/mcp/example.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 项目根目录和 MCP 服务器脚本路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
SERVER_SCRIPT = Path(__file__).parent / "server.py"


def show_result(name: str, result) -> None:
    """打印一次工具调用的结果 (兼容 mcp 1.x 的 isError 和 2.x 的 is_error)"""
    text = result.content[0].text if result.content else ""
    is_error = getattr(result, "is_error", getattr(result, "isError", False))
    status = "❌" if is_error else "✅"
    print(f"  {name} {status}: {text[:200]}")


async def main() -> None:
    # 1. 配置 stdio 服务器: 启动一个 server.py 子进程
    #    注意: 子进程默认不继承 PYTHONPATH, 需要显式传入,
    #    否则 server.py 里 `from tools.builtins...` 的导入会失败
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
        env={"PYTHONPATH": str(PROJECT_ROOT)},
    )

    # 2. 连接服务器并初始化会话
    #    注意: stdio_client 和 ClientSession 都是异步上下文管理器,
    #    所有工具调用都必须在 with 块内完成, 离开 with 块连接即关闭
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 3. 列出服务器上的所有工具
            tools_result = await session.list_tools()
            print("可用工具:", [tool.name for tool in tools_result.tools])

            # 4. 调用工具
            print("\n调用工具:")
            result = await session.call_tool("add", {"a": 3, "b": 4})
            show_result("add(3, 4)", result)

            result = await session.call_tool("multiply", {"a": 5, "b": 6})
            show_result("multiply(5, 6)", result)

            # 5. 调用联网搜索工具 (需要网络)
            result = await session.call_tool(
                "search", {"query": "Model Context Protocol", "max_results": 3}
            )
            show_result("search(...)", result)


if __name__ == "__main__":
    asyncio.run(main())
