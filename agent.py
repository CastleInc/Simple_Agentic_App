"""
LLM Agent with Function Agent and MCP Client capabilities.
This agent can handle user queries and route them to appropriate MCP tools.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp_config import mcp_config, MCPServerConfig
from prompts import get_system_prompt

# Load environment variables
load_dotenv()

# Initialize OpenAI client with configurable base URL
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


class CVEAgent:
    """
    An LLM-powered agent that acts as both a function agent and MCP client.
    It intelligently routes user queries to the appropriate CVE query tools.
    Supports multiple MCP servers and configurable system prompts.
    """

    def __init__(self, system_prompt_type: str = "default", model_name: Optional[str] = None):
        """
        Initialize the CVE Agent.

        Args:
            system_prompt_type: Type of system prompt to use (default, concise, detailed, analytics)
            model_name: OpenAI model name (defaults to env variable)
        """
        self.model = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        self.system_prompt = get_system_prompt(system_prompt_type)
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: List[Dict] = []
        self.server_contexts: Dict[str, tuple] = {}  # Store contexts for cleanup

        print(f"🤖 Agent initialized with model: {self.model}")
        print(f"📝 Using system prompt: {system_prompt_type}")

    async def __aenter__(self):
        """Enter the async context manager."""
        await self.connect_to_mcp_servers()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        await self.disconnect()

    async def connect_to_mcp_servers(self):
        """Connect to all enabled MCP servers and retrieve their tools."""
        enabled_servers = mcp_config.get_enabled_servers()

        if not enabled_servers:
            print("⚠️  No MCP servers enabled!")
            return

        print(f"\n🔌 Connecting to {len(enabled_servers)} MCP server(s)...")

        for server_config in enabled_servers:
            try:
                await self._connect_to_server(server_config)
                print(f"  ✅ Connected to: {server_config.name}")
            except Exception as e:
                print(f"  ❌ Failed to connect to {server_config.name}: {e}")

        print(f"\n📚 Total tools available: {len(self.available_tools)}")

    async def _connect_to_server(self, config: MCPServerConfig):
        """Connect to a single MCP server."""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=None
        )

        # Store the context managers
        stdio_context = stdio_client(server_params)
        stdio, write = await stdio_context.__aenter__()

        session_context = ClientSession(stdio, write)
        session = await session_context.__aenter__()

        await session.initialize()

        # List available tools from this server
        tools_response = await session.list_tools()
        server_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": f"[{config.name}] {tool.description}",
                    "parameters": tool.inputSchema
                },
                "_server": config.name  # Track which server provides this tool
            }
            for tool in tools_response.tools
        ]

        self.available_tools.extend(server_tools)
        self.sessions[config.name] = session
        self.server_contexts[config.name] = (stdio_context, session_context)

    async def disconnect(self):
        """Disconnect from all MCP servers."""
        print("\n🔌 Disconnecting from MCP servers...")
        for server_name, (stdio_ctx, session_ctx) in self.server_contexts.items():
            try:
                await session_ctx.__aexit__(None, None, None)
                await stdio_ctx.__aexit__(None, None, None)
                print(f"  ✅ Disconnected from: {server_name}")
            except Exception as e:
                print(f"  ⚠️  Error disconnecting from {server_name}: {e}")

    def convert_tools_to_openai_format(self) -> List[Dict]:
        """Convert MCP tools to OpenAI's tool format."""
        # Remove internal _server field before sending to OpenAI
        return [
            {k: v for k, v in tool.items() if k != "_server"}
            for tool in self.available_tools
        ]

    async def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool call via the appropriate MCP server."""
        # Find which server provides this tool
        server_name = None
        for tool in self.available_tools:
            if tool["function"]["name"] == tool_name:
                server_name = tool.get("_server")
                break

        if not server_name or server_name not in self.sessions:
            return f"Error: Tool {tool_name} not found or server not connected"

        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, tool_input)

        # Extract text content from result
        if result.content:
            return "\n".join([
                item.text if hasattr(item, 'text') else str(item)
                for item in result.content
            ])
        return "No result returned"

    async def chat(self, user_query: str, max_iterations: int = 5) -> tuple[str, list]:
        """
        Process user query using LLM with tool calling capabilities.
        The agent will iteratively call tools as needed to answer the query.
        Returns: (response_text, tool_results_list)
        """
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": user_query
            }
        ]

        tools = self.convert_tools_to_openai_format()
        all_tool_results = []  # Store all raw tool results for formatting

        for iteration in range(max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")

            # Call OpenAI with tool use
            response = openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            print(f"Finish reason: {response.choices[0].finish_reason}")

            # Check if we're done
            if response.choices[0].finish_reason == "stop":
                return response_message.content, all_tool_results

            # Process tool calls
            if response_message.tool_calls:
                # Add assistant's response to messages
                messages.append(response_message)

                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)

                    print(f"Calling tool: {tool_name}")
                    print(f"Tool input: {json.dumps(tool_input, indent=2)}")

                    # Execute tool via MCP
                    tool_result = await self.process_tool_call(tool_name, tool_input)

                    print(f"Tool result preview: {tool_result[:200]}...")

                    # Store raw tool results for Jinja2 formatting
                    all_tool_results.append({
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_result": tool_result
                    })

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
            else:
                # Unexpected finish reason
                return f"Unexpected finish reason: {response.choices[0].finish_reason}", all_tool_results

        return "Max iterations reached without completing the query.", all_tool_results

    async def run_interactive(self):
        """Run the agent in interactive mode."""
        print("=" * 60)
        print("CVE Query Agent - Interactive Mode")
        print("=" * 60)
        print("\nConnecting to MCP servers...")

        async with self:
            print("\n✓ All systems ready!")
            print("\nYou can ask questions about CVE vulnerabilities.")
            print("Examples:")
            print("  - Show me critical CVEs")
            print("  - Find CVE-2020-000001")
            print("  - What are the CVEs with CVSS score above 9?")
            print("  - Show me CVEs affecting Red Hat products")
            print("  - Give me statistics on all CVEs")
            print("\nType 'quit' or 'exit' to stop.\n")

            while True:
                try:
                    user_input = input("\n🧑 You: ").strip()

                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("\nGoodbye!")
                        break

                    if not user_input:
                        continue

                    print("\n🤖 Agent: Processing your query...")
                    response, _ = await self.chat(user_input)
                    print(f"\n🤖 Agent: {response}")

                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")


async def main():
    """Main entry point for the agent."""
    agent = CVEAgent()
    await agent.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
