"""
Streamlit Web Interface for CVE Query Agent
"""

import streamlit as st
import asyncio
import os
from agent import MCPClient
from dotenv import load_dotenv
from jinja_renderer import JinjaRenderer
from styles import get_custom_css
from prompts import get_system_prompt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops in Streamlit
import nest_asyncio
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="CVE Query Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Jinja2 Renderer
renderer = JinjaRenderer()

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


# Initialize session state for MCPClient
if 'mcp_client' not in st.session_state:
    st.session_state.mcp_client = None
if 'agent_ready' not in st.session_state:
    st.session_state.agent_ready = False


def run_async(coro):
    """Helper function to run async code in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If loop is already running (Streamlit context), use nest_asyncio
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)


async def initialize_agent():
    """Initialize the MCP agent if not already initialized."""
    if st.session_state.mcp_client is None or not st.session_state.agent_ready:
        try:
            logger.info("Initializing MCP Client...")
            client = MCPClient()
            await client.setup_agent()
            st.session_state.mcp_client = client
            st.session_state.agent_ready = True
            logger.info("✓ MCP Client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    return st.session_state.mcp_client


async def process_query_async(query: str):
    """Process a query using the MCP client."""
    try:
        client = await initialize_agent()
        response = await client.process_query(query)
        return response
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise


def main():
    """Main Streamlit application."""

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 CVE Query Agent</h1>
        <p>AI-Powered Vulnerability Intelligence System</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("📋 Query Options")

        query_type = st.selectbox(
            "Quick Query Templates",
            [
                "Custom Query",
                "Show all critical CVEs",
                "Find CVEs with CVSS > 9.0",
                "Search by CVE number",
                "CVEs with known exploits",
                "CISA KEV vulnerabilities",
                "Get CVE statistics",
                "Search by keyword",
                "Search by product"
            ]
        )

        st.divider()

        # System Prompt Selection
        st.header("🎯 Agent Behavior")
        prompt_type = st.selectbox(
            "Analysis Style",
            ["default", "concise", "detailed", "analytics"],
            help="Choose the agent's analysis style and depth"
        )

        # Show selected prompt preview
        with st.expander("📝 View System Prompt"):
            st.text_area(
                "Current System Prompt",
                get_system_prompt(prompt_type),
                height=200,
                disabled=True
            )

        st.divider()

        st.header("ℹ️ About")
        st.info(f"""
        This application uses:
        - **{os.getenv('LLM_MODEL_NAME', 'llama3.1')}** for intelligent query processing
        - **MCP Server** for tool routing
        - **MongoDB** for CVE data storage
        - **Jinja2** for beautiful templates
        """)

        st.divider()

        # Connection status
        if os.getenv("LLM_BASE_URL"):
            st.success("✅ LLM endpoint configured")
        else:
            st.warning("⚠️ LLM endpoint not set")

        if os.getenv("MONGODB_URI"):
            st.success("✅ MongoDB configured")
        else:
            st.error("❌ MongoDB URI missing")

        # Model info
        st.divider()
        st.caption(f"🤖 Model: {os.getenv('LLM_MODEL_NAME', 'llama3.1')}")
        if os.getenv('LLM_BASE_URL') and os.getenv('LLM_BASE_URL') != "https://api.openai.com/v1":
            st.caption(f"🔗 Custom endpoint: {os.getenv('LLM_BASE_URL')}")

        # Agent status
        if st.session_state.agent_ready:
            if st.session_state.mcp_client:
                tools_count = len(st.session_state.mcp_client.tools)
                st.success(f"✅ Agent ready ({tools_count} tools)")
        else:
            st.info("🔄 Agent will initialize on first query")

        # Add a button to manually initialize
        if st.button("🚀 Initialize Agent Now"):
            with st.spinner("Initializing agent..."):
                try:
                    run_async(initialize_agent())
                    st.success("✅ Agent initialized!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to initialize: {str(e)}")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("💬 Ask a Question")

        # Build query based on template
        if query_type == "Custom Query":
            user_query = st.text_area(
                "Enter your query:",
                placeholder="e.g., Show me all critical CVEs affecting Red Hat products",
                height=100
            )
        elif query_type == "Search by CVE number":
            cve_number = st.text_input("Enter CVE number:", placeholder="CVE-2020-000001")
            user_query = f"Find {cve_number}" if cve_number else ""
        elif query_type == "Search by keyword":
            keyword = st.text_input("Enter keyword:", placeholder="Buffer Overflow")
            user_query = f"Search for CVEs related to {keyword}" if keyword else ""
        elif query_type == "Search by product":
            product = st.text_input("Enter product name:", placeholder="Red Hat")
            user_query = f"Show me CVEs affecting {product}" if product else ""
        else:
            user_query = query_type

        submit_button = st.button("🚀 Submit Query", use_container_width=True)

    with col2:
        st.header("📊 Quick Stats")
        st.markdown("""
        <div class="stat-card">
            <h3 style="color: #667eea; margin: 0;">10</h3>
            <p style="margin: 0;">CVE Query Tools</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <div class="stat-card">
            <h3 style="color: #764ba2; margin: 0;">Ollama</h3>
            <p style="margin: 0;">Powered by Llama 3.1</p>
        </div>
        """, unsafe_allow_html=True)

    # Process query
    if submit_button and user_query:
        with st.spinner("🔄 Processing your query..."):
            try:
                # Process the query using our helper function
                response = run_async(process_query_async(user_query))

                # Display results
                st.success("✅ Query completed!")
                st.divider()

                # Render the response using Jinja2 templates
                st.subheader("🤖 AI Analysis")

                try:
                    # Use the renderer to create beautiful HTML from JSON response
                    rendered_html = renderer.render_response(response)

                    # Use st.html() for better HTML rendering (Streamlit 1.30+)
                    # or use components.html() for older versions
                    import streamlit.components.v1 as components
                    components.html(rendered_html, height=800, scrolling=True)

                except Exception as render_error:
                    logger.warning(f"Failed to render with template: {render_error}")
                    logger.exception(render_error)
                    # Fallback to displaying as markdown if rendering fails
                    st.markdown(response)

                # Show raw response in expander
                with st.expander("🔍 View Raw Response"):
                    st.code(response, language="json")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.exception("Query processing failed")

                # Show helpful error message
                st.info("""
                **Troubleshooting tips:**
                - Make sure MongoDB is running
                - Check that Ollama is running: `ollama serve`
                - Verify your .env configuration
                - Try reinitializing the agent using the sidebar button
                """)

    # Example queries section
    st.divider()
    st.header("💡 Example Queries")

    examples_col1, examples_col2, examples_col3 = st.columns(3)

    with examples_col1:
        st.markdown("""
        **By Severity:**
        - Show me critical CVEs
        - Find high severity vulnerabilities
        - List medium severity CVEs
        """)

    with examples_col2:
        st.markdown("""
        **By Properties:**
        - CVEs with CVSS score > 9
        - Find CVEs with known exploits
        - Show CISA KEV vulnerabilities
        """)

    with examples_col3:
        st.markdown("""
        **By Search:**
        - Find CVE-2020-000001
        - Search for Buffer Overflow
        - Show Red Hat CVEs
        """)


if __name__ == "__main__":
    main()
