"""
Streamlit Web Interface for CVE Query Agent
"""

import streamlit as st
import asyncio
import os
import json
from agent import CVEAgent
from dotenv import load_dotenv
from jinja_renderer import JinjaRenderer
from styles import get_custom_css
from prompts import get_system_prompt

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
        if os.getenv("LLM_API_KEY"):
            st.success("✅ LLM API Key configured")
        else:
            st.error("❌ LLM API Key missing")

        if os.getenv("MONGODB_URI"):
            st.success("✅ MongoDB configured")
        else:
            st.error("❌ MongoDB URI missing")

        # Model info
        st.divider()
        st.caption(f"🤖 Model: {os.getenv('LLM_MODEL_NAME', 'llama3.1')}")
        if os.getenv('LLM_BASE_URL') and os.getenv('LLM_BASE_URL') != "https://api.openai.com/v1":
            st.caption(f"🔗 Custom endpoint: {os.getenv('LLM_BASE_URL')}")

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
            <h3 style="color: #764ba2; margin: 0;">OpenAI</h3>
            <p style="margin: 0;">Powered by GPT-4</p>
        </div>
        """, unsafe_allow_html=True)

    # Process query
    if submit_button and user_query:
        with st.spinner("🔄 Processing your query..."):
            try:
                # Define async function to run the entire process
                async def run_query_with_agent():
                    # Use agent with selected system prompt
                    async with CVEAgent(system_prompt_type=prompt_type) as agent:
                        response, tool_results = await agent.chat(user_query)
                        return response, tool_results

                # Create and run event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response, tool_results = loop.run_until_complete(run_query_with_agent())
                loop.close()

                # Display results
                st.success("✅ Query completed!")
                st.divider()

                # Check if we have tool results with CVE data
                has_cve_data = False

                for tool_result in tool_results:
                    raw_result = tool_result.get("tool_result", "")

                    # Try to parse the tool result as JSON
                    try:
                        result_data = json.loads(raw_result)

                        # Check if it's a single CVE
                        if isinstance(result_data, dict) and 'cve_number' in result_data:
                            has_cve_data = True
                            st.subheader("📄 CVE Details")
                            # Use components.html to properly render HTML without showing raw code
                            import streamlit.components.v1 as components
                            cve_html = renderer.render_cve_card(result_data)
                            components.html(cve_html, height=800, scrolling=True)

                        # Check if it's multiple CVEs
                        elif isinstance(result_data, dict) and 'results' in result_data:
                            has_cve_data = True
                            st.subheader(f"📄 Found {result_data.get('count', 0)} CVE(s)")

                            import streamlit.components.v1 as components
                            for cve in result_data.get('results', []):
                                cve_html = renderer.render_cve_card(cve)
                                components.html(cve_html, height=800, scrolling=True)

                        # For statistics or other data
                        elif isinstance(result_data, dict) and not has_cve_data:
                            import streamlit.components.v1 as components
                            response_html = renderer.render_response(user_query, json.dumps(result_data, indent=2))
                            components.html(response_html, height=400, scrolling=True)
                            has_cve_data = True

                    except json.JSONDecodeError:
                        continue

                # If no CVE data was formatted, show the LLM's text response
                if not has_cve_data and response:
                    st.subheader("🤖 AI Analysis")
                    st.markdown(response)

                # Also show the LLM's analysis/summary if we formatted CVE cards
                elif has_cve_data and response:
                    st.divider()
                    st.subheader("🤖 AI Analysis")
                    st.markdown(response)

                # Show raw response in expander
                with st.expander("🔍 View Raw Data"):
                    st.subheader("Tool Results:")
                    for i, tool_result in enumerate(tool_results, 1):
                        st.write(f"**Tool {i}: {tool_result['tool_name']}**")
                        st.code(tool_result['tool_result'], language="json")

                    st.subheader("LLM Response:")
                    st.write(response)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

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