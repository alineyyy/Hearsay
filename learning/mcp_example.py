"""
MCP 集成示例：让 agent 通过 MCP 调用外部工具服务

这里接的是 AWS 官方提供的 "AWS Documentation MCP Server"：
一个专门用来查询 AWS 官方文档的 MCP 服务，不需要额外申请 API key。
运行它靠的是 `uvx`（uv 自带的一次性运行工具的命令，会自动下载并运行这个 MCP server）。

运行方式：
  python3 -u mcp_example.py

第一次运行会比较慢，因为 uvx 要先下载这个 MCP server 包。
"""

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# 1. 定义怎么启动这个 MCP server：本质是本地起一个子进程，
#    Strands 通过标准输入输出(stdio)和它"说话"，这就是 MCP 协议的一种传输方式。
aws_docs_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"],
    )
))

# 2. 注意：MCP 连接必须在 `with` 代码块里用，
#    出了这个 block 连接就断了，agent 也就没法再调用这些工具了。
with aws_docs_client:
    tools = aws_docs_client.list_tools_sync()
    print(f"这个 MCP server 提供了 {len(tools)} 个工具：",
          [t.tool_name for t in tools])

    agent = Agent(tools=tools)
    agent("AWS Lambda 是什么？帮我查一下官方文档给个简短解释。")
