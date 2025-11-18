import logging
import os
from dataclasses import dataclass
import time
from typing import Any, List, Optional
import sys
import asyncio

from dotenv import load_dotenv
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai_like import OpenAILike
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

load_dotenv()
load_dotenv("/vault-secrets/.env", override=True)


@dataclass
class Messages:
    actor: str
    payload: str


USER = "user"
ASSISTANT = "ai"
MESSAGES = "messages"


class MCPClient:
    """
    A client for interacting with the MCP (Model Context Protocol) server.

    This class is responsible for setting up the connection to the MCP server,
    initializing the tools and LLM (Language Learning Model),
    and processing user queries using the configured agent.

    Attributes:
        model_endpoint (str): The endpoint for the LLM model.
        model_name (str): The name of the LLM model.
        temperature (float): The temperature setting for the LLM model.
        agent (ReActAgent): The agent used to process queries.
        tools (list): A list of tools fetched from the MCP server.
        mcp_session (ClientSession): Active MCP session.
    """

    def __init__(self) -> None:
        """
        Initializes the MCPClient with default settings and environment vars.
        """
        self.model_endpoint = os.environ.get("LLM_MODEL_HOST") or os.environ.get("LLM_BASE_URL", "")
        self.model_name = os.environ.get("LLM_MODEL_NAME", "")
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
        self.agent: Optional[ReActAgent] = None
        self.tools: List[FunctionTool] = []
        self.mcp_session: Optional[ClientSession] = None
        self.exit_stack = None

    async def _connect_to_mcp_server(self) -> ClientSession:
        """Connect to the local MCP server via stdio."""
        try:
            # Get the absolute path to mcp_server.py
            server_script = os.path.join(os.getcwd(), "mcp_server.py")

            if not os.path.exists(server_script):
                raise FileNotFoundError(f"MCP server script not found: {server_script}")

            logger.info(f"Starting MCP server: {sys.executable} {server_script}")

            # Use sys.executable to get the current Python interpreter
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_script],
                env=None
            )

            # Create stdio connection
            from contextlib import AsyncExitStack
            self.exit_stack = AsyncExitStack()

            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport

            # Create session
            self.mcp_session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # Initialize the session
            await self.mcp_session.initialize()

            logger.info("✓ MCP session initialized successfully")
            return self.mcp_session

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise

    async def _load_mcp_tools(self) -> List[FunctionTool]:
        """Load tools from MCP server and convert to LlamaIndex FunctionTools."""
        if not self.mcp_session:
            raise RuntimeError("MCP session not initialized")

        try:
            # List available tools from MCP server
            logger.info("Fetching tools from MCP server...")
            response = await self.mcp_session.list_tools()

            logger.info(f"Found {len(response.tools)} tools from MCP server")

            llama_tools = []
            for tool in response.tools:
                # Create a LlamaIndex FunctionTool for each MCP tool
                llama_tool = self._create_llama_tool(tool)
                llama_tools.append(llama_tool)
                logger.info(f"  ✓ Loaded: {tool.name}")

            return llama_tools

        except Exception as e:
            logger.error(f"Error loading MCP tools: {str(e)}")
            raise

    def _create_llama_tool(self, mcp_tool: Any) -> FunctionTool:
        """Convert an MCP tool to a LlamaIndex FunctionTool."""
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description or f"Tool: {tool_name}"

        # Create an async wrapper function
        async def tool_function(**kwargs) -> str:
            """Wrapper function that calls the MCP tool."""
            try:
                if not self.mcp_session:
                    return "Error: MCP session not available"

                # Call the MCP tool
                result = await self.mcp_session.call_tool(tool_name, arguments=kwargs)

                # Extract text content from result
                if hasattr(result, 'content') and result.content:
                    text_parts = []
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            text_parts.append(content_item.text)
                    return "\n".join(text_parts) if text_parts else str(result)

                return str(result)

            except Exception as e:
                logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
                return f"Error: {str(e)}"

        # Create sync wrapper for LlamaIndex
        def sync_wrapper(**kwargs) -> str:
            """Sync wrapper that runs the async function."""
            try:
                # Get or create event loop
                try:
                    loop = asyncio.get_running_loop()
                    # If we're in a running loop, use nest_asyncio
                    import nest_asyncio
                    nest_asyncio.apply()
                    return loop.run_until_complete(tool_function(**kwargs))
                except RuntimeError:
                    # No running loop, create new one
                    return asyncio.run(tool_function(**kwargs))
            except Exception as e:
                logger.error(f"Error in sync wrapper for {tool_name}: {str(e)}")
                return f"Error: {str(e)}"

        # Create the FunctionTool - don't pass fn_schema as LlamaIndex will infer it
        # The MCP inputSchema is already a dict and LlamaIndex expects a Pydantic model
        return FunctionTool.from_defaults(
            fn=sync_wrapper,
            name=tool_name,
            description=tool_description,
        )

    async def setup_agent(self) -> None:
        """
        Sets up the FunctionAgent for processing queries.
        Connects to MCP server, fetches tools, and initializes the LLM.
        """
        if self.agent is not None:
            return

        start_time = time.perf_counter()
        try:
            logger.info("Setting up MCP agent...")

            # Connect to MCP server and load tools
            if not self.tools:
                logger.info("Connecting to MCP server...")
                await self._connect_to_mcp_server()

                logger.info("Loading tools from MCP server...")
                self.tools = await self._load_mcp_tools()

                logger.info(f"✓ Loaded {len(self.tools)} tools successfully")

            # Initialize LLM
            llm_start = time.perf_counter()
            logger.info(f"Initializing LLM with model {self.model_name}...")

            if not self.model_endpoint:
                raise ValueError("LLM endpoint not configured. Set LLM_MODEL_HOST or LLM_BASE_URL in .env")

            logger.info(f"Connecting to LLM at: {self.model_endpoint}")

            # Clear OpenAI environment variables to avoid conflicts
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("OPENAI_BASE_URL", None)

            # Create a custom OpenAI client for local models
            from openai import AsyncOpenAI

            custom_client = AsyncOpenAI(
                api_key="sk-111111111111111111111111111111111111111111111111",  # Properly formatted dummy key
                base_url=self.model_endpoint,
                timeout=120.0,
            )

            llm = OpenAILike(
                model=self.model_name,
                max_tokens=4096,
                is_chat_model=True,
                is_function_calling_model=False,  # Ollama llama3.1 doesn't support native function calling
                temperature=self.temperature,
                async_openai_client=custom_client,  # Pass our custom client
            )

            llm_end = time.perf_counter()
            logger.info(f"LLM initialized in {(llm_end - llm_start):.2f}s")

            # Create ReActAgent with tools - it will use text-based reasoning instead of function calling
            system_prompt = """You are a CVE security analyst assistant. You have access to various tools to query a CVE vulnerability database.

When the user asks about CVEs:
1. Use the available tools to query the database
2. Present results clearly and concisely
3. Highlight critical information like severity, CVSS scores, and exploit status

Available tools allow you to:
- query_cve_by_severity: Query CVEs by severity level (CRITICAL, HIGH, MEDIUM, LOW)
- query_cve_by_number: Query specific CVE by its number
- query_cve_by_cvss_range: Query CVEs within a CVSS score range
- query_cve_by_keyword: Search CVEs by keywords
- query_cve_by_product: Search CVEs affecting specific products
- query_cve_with_exploit: Find CVEs with known exploits
- query_cve_by_cisa_key: Find CVEs in CISA KEV catalog
- get_cve_statistics: Get statistical summaries
- query_cve_by_attack_type: Query by attack vector or complexity
- query_recent_cves: Get recently published CVEs

Always use the tools to get accurate data from the database."""

            self.agent = ReActAgent(
                tools=self.tools,
                llm=llm,
                verbose=True,
                max_iterations=10,
            )

            logger.info("✓ Agent setup completed successfully!")

        except Exception as e:
            logger.error(f"Error setting up agent: {str(e)}")
            raise
        finally:
            end_time = time.perf_counter()
            logger.info(f"Setup completed in {end_time - start_time:.2f}s")

    async def process_query(self, user_query: str) -> str:
        """
        Process a user query using intelligent tool routing.

        Args:
            user_query: The query provided by the user

        Returns:
            str: The response generated by the agent
        """
        if self.agent is None:
            await self.setup_agent()

        try:
            query_start = time.perf_counter()
            logger.info(f"Processing query: {user_query}")

            # Simple intelligent routing based on query patterns
            query_lower = user_query.lower()

            # Route to appropriate tool based on query content
            result = None

            # Check for CVE number pattern (CVE-YYYY-NNNNN)
            import re
            cve_pattern = r'cve-\d{4}-\d{4,7}'
            cve_match = re.search(cve_pattern, query_lower)

            if cve_match:
                cve_number = cve_match.group(0).upper()
                logger.info(f"Detected CVE number: {cve_number}")
                # Find and call the CVE number query tool
                for tool in self.tools:
                    if tool.metadata.name == "query_cve_by_number":
                        logger.info(f"Calling tool: query_cve_by_number with cve_number={cve_number}")
                        result = str(tool(cve_number=cve_number))
                        break

            elif "statistic" in query_lower or "summary" in query_lower or "overview" in query_lower:
                logger.info("Detected statistics query")
                for tool in self.tools:
                    if tool.metadata.name == "get_cve_statistics":
                        logger.info("Calling tool: get_cve_statistics")
                        result = str(tool())
                        break

            elif "critical" in query_lower:
                logger.info("Detected CRITICAL severity query")
                limit = 5  # Default limit
                for tool in self.tools:
                    if tool.metadata.name == "query_cve_by_severity":
                        logger.info(f"Calling tool: query_cve_by_severity with severity=CRITICAL, limit={limit}")
                        result = str(tool(severity="CRITICAL", limit=limit))
                        break

            elif "high" in query_lower and "severity" in query_lower:
                logger.info("Detected HIGH severity query")
                limit = 5
                for tool in self.tools:
                    if tool.metadata.name == "query_cve_by_severity":
                        logger.info(f"Calling tool: query_cve_by_severity with severity=HIGH, limit={limit}")
                        result = str(tool(severity="HIGH", limit=limit))
                        break

            elif "exploit" in query_lower:
                logger.info("Detected exploit query")
                limit = 5
                for tool in self.tools:
                    if tool.metadata.name == "query_cve_with_exploit":
                        logger.info(f"Calling tool: query_cve_with_exploit with limit={limit}")
                        result = str(tool(limit=limit))
                        break

            elif "recent" in query_lower or "latest" in query_lower:
                logger.info("Detected recent CVE query")
                limit = 5
                for tool in self.tools:
                    if tool.metadata.name == "query_recent_cves":
                        logger.info(f"Calling tool: query_recent_cves with limit={limit}")
                        result = str(tool(limit=limit))
                        break

            elif "cisa" in query_lower or "kev" in query_lower:
                logger.info("Detected CISA KEV query")
                limit = 5
                for tool in self.tools:
                    if tool.metadata.name == "query_cve_by_cisa_key":
                        logger.info(f"Calling tool: query_cve_by_cisa_key with limit={limit}")
                        result = str(tool(limit=limit))
                        break

            else:
                # Try keyword search as fallback
                logger.info("Using keyword search as fallback")
                # Extract potential keywords (simple approach)
                keywords = [word for word in query_lower.split() if len(word) > 3 and word not in ['find', 'show', 'give', 'list', 'query', 'search', 'with', 'that', 'have']]
                if keywords:
                    keyword = keywords[0]
                    logger.info(f"Searching with keyword: {keyword}")
                    for tool in self.tools:
                        if tool.metadata.name == "query_cve_by_keyword":
                            logger.info(f"Calling tool: query_cve_by_keyword with keyword={keyword}, limit=5")
                            result = str(tool(keyword=keyword, limit=5))
                            break

            if not result:
                result = "I couldn't determine which tool to use for your query. Please try:\n" \
                        "- Searching for a specific CVE (e.g., 'Find CVE-2020-000001')\n" \
                        "- Asking for statistics (e.g., 'Show CVE statistics')\n" \
                        "- Querying by severity (e.g., 'Show CRITICAL CVEs')\n" \
                        "- Finding exploits (e.g., 'Show CVEs with exploits')\n" \
                        "- Getting recent CVEs (e.g., 'Show recent CVEs')"

            query_end = time.perf_counter()
            logger.info(f"Query processed in {query_end - query_start:.2f}s")

            return result

        except Exception as query_error:
            logger.exception(f"Error processing query: {query_error}")
            return (
                "I'm sorry, but I was unable to process your query. "
                "Please try again or contact support if the issue persists."
            )

    async def cleanup(self):
        """Cleanup MCP connections."""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
                self.exit_stack = None
                logger.info("✓ MCP connections closed")
        except Exception as e:
            # Silently ignore "Event loop is closed" errors during shutdown
            if "Event loop is closed" not in str(e) and "closed" not in str(e).lower():
                logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup - silently handles all errors."""
        if self.exit_stack:
            try:
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = None
                except (RuntimeError, AttributeError):
                    loop = None

                if loop is None:
                    # Create a new loop only if we really need to
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.cleanup())
                        loop.close()
                    except Exception:
                        # Silently ignore all cleanup errors
                        pass
            except Exception:
                # Silently ignore all errors during destructor
                pass
