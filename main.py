"""
Simple Agentic Application - Main Entry Point

This application demonstrates an LLM agent with MCP server capabilities
for querying CVE (vulnerability) data from MongoDB.

Usage:
    python main.py                    # Run interactive agent
    python main.py --demo             # Run demo queries
    python main.py --server           # Run MCP server only
    python main.py --streamlit        # Run Streamlit web interface
"""

import asyncio
import sys
import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
    """Print application banner."""
    print("=" * 70)
    print(" " * 15 + "CVE Query Agentic Application")
    print("=" * 70)
    print("\n🔍 LLM Agent + MCP Server for CVE Vulnerability Queries")
    print("\n📋 Features:")
    print("  • Query CVEs by number, severity, CVSS score, keywords, products")
    print("  • Filter by exploits and CISA KEV status")
    print("  • Get statistical analysis of vulnerability data")
    print("  • Natural language query processing with Claude AI")
    print("=" * 70)
    print()


async def run_interactive_agent():
    """Run the agent in interactive mode."""
    from agent import MCPClient
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    client = MCPClient()
    print("\n🤖 Starting interactive agent...")
    print("Type your CVE-related queries below.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}:
                print("\nGoodbye!")
                break
            if not user_input:
                continue

            print("\n🤖 Agent: Processing your query...")
            response = await client.process_query(user_input)
            print(f"\n🤖 Agent: {response}")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def run_demo_queries():
    """Run demonstration queries to showcase capabilities."""
    from agent import MCPClient

    print("\n🎬 Running Demo Queries...\n")

    demo_queries = [
        "Show me statistics on all CVEs in the database",
        "Find all critical severity CVEs, limit to 3",
        "What CVEs have a CVSS score between 9.0 and 10.0?",
        "Search for CVEs related to 'Directory Traversal'",
    ]

    client = MCPClient()

    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'='*70}")
        print(f"Demo Query {i}: {query}")
        print('='*70)

        try:
            response = await client.process_query(query)
            print(f"\n✅ Response:\n{response}")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

        if i < len(demo_queries):
            print("\n⏸️  Press Enter for next query...")
            input()


def run_mcp_server():
    """Run the MCP server standalone."""
    import subprocess

    print("\n🚀 Starting MCP Server...")
    print("The server will run in stdio mode for MCP communication.\n")

    try:
        subprocess.run([sys.executable, "mcp_server.py"])
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped by user")


def run_streamlit():
    """Run the Streamlit web interface."""
    print("\n🌐 Starting Streamlit Web Interface...")
    print("Opening in your default browser...\n")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
    except KeyboardInterrupt:
        print("\n\n✋ Streamlit stopped by user")


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["LLM_API_KEY", "MONGODB_URI"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("\n⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please create a .env file with the required variables.")
        print("   See .env.example for reference.\n")
        return False

    return True


def print_help():
    """Print usage help."""
    print("\nUsage:")
    print("  python main.py              # Run interactive agent")
    print("  python main.py --demo       # Run demo queries")
    print("  python main.py --server     # Run MCP server only")
    print("  python main.py --streamlit  # Run Streamlit web interface")
    print("  python main.py --help       # Show this help")
    print()


def main():
    """Main entry point."""
    print_banner()

    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['--help', '-h']:
            print_help()
            return

        elif arg == '--server':
            run_mcp_server()
            return

        elif arg == '--streamlit':
            if not check_environment():
                sys.exit(1)
            run_streamlit()
            return

        elif arg == '--demo':
            if not check_environment():
                sys.exit(1)
            asyncio.run(run_demo_queries())
            return

        else:
            print(f"❌ Unknown argument: {arg}")
            print_help()
            sys.exit(1)

    # Default: run interactive agent
    if not check_environment():
        sys.exit(1)

    asyncio.run(run_interactive_agent())


if __name__ == '__main__':
    main()
