# Simple Agentic Application with MCP Server

A sophisticated LLM-powered agent that queries CVE (Common Vulnerabilities and Exposures) data from MongoDB using the Model Context Protocol (MCP) with a beautiful Streamlit web interface.

## 🚀 New Features

- **🤖 Configurable System Prompts**: Choose between default, concise, detailed, or analytics analysis styles
- **🔧 Multiple MCP Servers**: Support for multiple specialized MCP servers (CVE, Weather, etc.)
- **⚙️ Flexible Model Configuration**: Configure model name and API base URL via environment variables
- **📊 Enhanced Analytics**: Choose agent behavior based on your needs
- **🎨 Clean Architecture**: Separated concerns with modular design

## Architecture

This application consists of multiple components:

1. **MCP Servers** (`mcp_server.py`, `mcp_weather_server.py`): Provide tools to query different data sources
2. **LLM Agent** (`agent.py`): Acts as both a function agent and MCP client with configurable behavior
3. **Streamlit Interface** (`streamlit_app.py`): Beautiful web UI with Jinja2 templates
4. **Configuration** (`mcp_config.py`, `prompts.py`): Centralized configuration and prompts

## Features

### System Prompts

Choose from 4 different agent personalities:

1. **Default** - Balanced security analyst with comprehensive analysis
2. **Concise** - Quick, to-the-point vulnerability reports
3. **Detailed** - In-depth technical analysis with business context
4. **Analytics** - Data-driven metrics and statistical insights

### Multiple MCP Servers

The agent can connect to multiple MCP servers simultaneously:
- **CVE Query Server**: 8 specialized tools for vulnerability data
- **Weather Server** (example): Demonstrates multi-server capability
- **Extensible**: Add more servers via environment configuration

### Model Configuration

- **Configurable Model**: Set via `OPENAI_MODEL_NAME` environment variable
- **Custom Endpoints**: Support for Azure OpenAI, custom deployments via `OPENAI_BASE_URL`
- **Flexible**: Works with any OpenAI-compatible API

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=genai_kb

# OpenAI Configuration
OPENAI_API_KEY=sk-...your_key_here...
OPENAI_MODEL_NAME=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# MCP Server Configuration
MCP_CVE_SERVER_ENABLED=true
MCP_CVE_SERVER_COMMAND=python
MCP_CVE_SERVER_ARGS=mcp_server.py

# Optional: Add more MCP servers
# MCP_WEATHER_SERVER_ENABLED=true
# MCP_WEATHER_SERVER_COMMAND=python
# MCP_WEATHER_SERVER_ARGS=mcp_weather_server.py
```

### 3. Ensure MongoDB is Running

Your MongoDB should contain a `cve_details` collection with CVE data.

## Usage

### Streamlit Web Interface (Recommended)

```bash
python main.py --streamlit
```

Or directly:

```bash
streamlit run streamlit_app.py
```

**New UI Features:**
- 🎯 **Analysis Style Selector**: Choose agent behavior in sidebar
- 📝 **System Prompt Preview**: View the active system prompt
- 🤖 **Model Info Display**: See which model is being used
- 🔗 **Endpoint Status**: Visual confirmation of custom endpoints

### Interactive CLI Mode

```bash
python main.py
```

The agent will automatically:
1. Load system prompt (default)
2. Connect to all enabled MCP servers
3. List available tools from each server
4. Start interactive query session

### Programmatic Usage with Custom Prompts

```python
import asyncio
from agent import CVEAgent

async def query_with_custom_prompt():
    # Use detailed analysis prompt
    agent = CVEAgent(system_prompt_type="detailed")
    
    async with agent:
        response, tool_results = await agent.chat(
            "Analyze CVE-2020-000001 in detail"
        )
        print(response)

asyncio.run(query_with_custom_prompt())
```

## Adding New MCP Servers

### Step 1: Create Your MCP Server

```python
# mcp_my_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("my-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(...)]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    # Your tool implementation
    pass
```

### Step 2: Add Configuration to `.env`

```env
MCP_MY_SERVER_ENABLED=true
MCP_MY_SERVER_COMMAND=python
MCP_MY_SERVER_ARGS=mcp_my_server.py
MCP_MY_SERVER_DESCRIPTION=My custom server description
```

### Step 3: Restart the Agent

The agent will automatically discover and connect to your new server!

## Project Structure

```
Simple_Agentic_App/
├── agent.py              # Multi-server LLM Agent with system prompts
├── mcp_server.py         # CVE query MCP server
├── mcp_weather_server.py # Example: Weather MCP server
├── mcp_config.py         # 🆕 MCP server configuration manager
├── prompts.py            # 🆕 System prompts library
├── streamlit_app.py      # Enhanced Streamlit UI
├── jinja_renderer.py     # Template rendering
├── styles.py             # CSS styles
├── templates/
│   ├── cve_card.html
│   └── response.html
├── requirements.txt
├── .env.example          # Updated with new options
└── README.md
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL_NAME` | Model to use | `gpt-4o` |
| `OPENAI_BASE_URL` | API endpoint URL | `https://api.openai.com/v1` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/` |
| `MONGODB_DATABASE` | Database name | `vulnerabilities` |
| `MCP_*_SERVER_ENABLED` | Enable/disable server | `true`/`false` |
| `MCP_*_SERVER_COMMAND` | Command to run server | `python` |
| `MCP_*_SERVER_ARGS` | Server script path | `mcp_server.py` |

### System Prompt Types

- `default`: Balanced analysis (recommended)
- `concise`: Brief, focused responses
- `detailed`: Comprehensive technical analysis
- `analytics`: Statistical and metrics-focused

## Advanced Usage

### Using Azure OpenAI

```env
OPENAI_API_KEY=your_azure_key
OPENAI_MODEL_NAME=gpt-4
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
```

### Custom Local Model

```env
OPENAI_API_KEY=local
OPENAI_MODEL_NAME=llama-3
OPENAI_BASE_URL=http://localhost:8000/v1
```

## License

This is a demonstration project for educational purposes.

## Features

### MCP Server Tools (10 Specialized Tools)

The CVE MCP server provides 10 individual `@app.tool()` decorated functions, each handling a specific type of query:

1. **query_cve_by_number** - Find CVE by specific CVE number
2. **query_cve_by_severity** - Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
3. **query_cve_by_cvss_range** - Query by CVSS score range
4. **query_cve_by_keyword** - Search in title, description, keywords
5. **query_cve_by_product** - Find CVEs affecting specific products
6. **query_cve_with_exploit** - Filter CVEs with known exploits
7. **query_cve_by_cisa_key** - Find CISA KEV vulnerabilities
8. **get_cve_statistics** - Get statistical summary of CVE data
9. **query_cve_by_attack_type** - 🆕 Query by attack/exploitation type
10. **query_recent_cves** - 🆕 Find recently modified or discovered CVEs

Each tool uses its own `@app.tool()` decorator for clean separation and individual documentation.
