"""
MCP: letting an agent call tools that live outside the process.

Kept from the first day of the project. Not part of Hearsay — the product lives in src/.

This connects to the AWS Documentation MCP Server: an official, free service that can
search and read AWS docs. Nothing to sign up for. `uvx` downloads and runs it on demand.

The thing worth noticing: a local @tool function and a remote MCP tool look identical to
the agent. That uniformity is the whole point of the protocol.

Run:
  python3 -u mcp_example.py

The first run is slow while uvx fetches the server.
"""

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Describes how to start the server: a local subprocess that Strands talks to over
# stdin/stdout. That is one of MCP's transports; HTTP and SSE are the others.
aws_docs_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"],
    )
))

# The connection has a lifetime. Outside this `with` block it is closed, and any tool
# call the agent tries will fail — a mistake worth making once to remember it.
with aws_docs_client:
    tools = aws_docs_client.list_tools_sync()
    print(f"This MCP server offers {len(tools)} tools:", [t.tool_name for t in tools])

    agent = Agent(tools=tools)
    agent("What is AWS Lambda? Check the official documentation and answer briefly.")
