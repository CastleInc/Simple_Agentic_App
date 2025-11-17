# Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `openai` - OpenAI GPT-4 SDK
- `pymongo` - MongoDB driver
- `python-dotenv` - Environment variable management
- `mcp` - Model Context Protocol library
- `streamlit` - Web interface framework
- `jinja2` - Template engine for beautiful responses

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=your_database_name
OPENAI_API_KEY=sk-...your_key_here...
```

**Note:** Since you already have MongoDB data, just configure the correct database name.

### 3. Run the Application

#### 🌐 Streamlit Web Interface (Recommended)

```bash
python main.py --streamlit
```

This launches a beautiful web interface with:
- 🎨 Modern UI with gradient design
- 🎯 Quick query templates
- 🎴 Formatted CVE cards using Jinja2
- 📊 Real-time statistics
- 🔍 Interactive search

#### 💻 Interactive CLI Mode
```bash
python main.py
```

This starts an interactive chat session with the agent.

#### 🎬 Demo Mode
```bash
python main.py --demo
```

Runs pre-configured demo queries to showcase capabilities.

#### 🔧 Server Only Mode
```bash
python main.py --server
```

Runs just the MCP server (useful for debugging).

## 📊 Sample Queries

Try these example queries in the Streamlit interface or CLI:

### By CVE Number:
- "Find CVE-2020-000001"
- "Show me details for CVE-2021-000002"

### By Severity:
- "List all critical CVEs"
- "Show me high severity vulnerabilities"

### By CVSS Score:
- "Find CVEs with CVSS score between 9.0 and 10.0"
- "Show me vulnerabilities with score above 8.0"

### By Keyword:
- "Search for Directory Traversal CVEs"
- "Find vulnerabilities related to Buffer Overflow"

### By Product:
- "Show me CVEs affecting Red Hat"
- "Find Apache vulnerabilities"
- "What Windows CVEs exist?"

### By Exploit Status:
- "Show me CVEs with known exploits"
- "Find CISA KEV vulnerabilities"

### Statistics:
- "Give me statistics on all CVEs"
- "How many critical CVEs are there?"

## 🏗️ Architecture Overview

```
┌─────────────────┐
│  Streamlit UI   │ ◄── Beautiful Jinja2 templates
│ (streamlit_app) │     for CVE cards & responses
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Agent     │ ◄── Uses OpenAI GPT-4
│   (agent.py)    │     for natural language understanding
└────────┬────────┘
         │
         │ MCP Protocol
         │
         ▼
┌─────────────────┐
│   MCP Server    │ ◄── 8 specialized tools
│ (mcp_server.py) │     with intelligent routing
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MongoDB       │ ◄── Your existing CVE data
│ (cve_details)   │
└─────────────────┘
```

## 🎨 Jinja2 Templates

The application uses two beautiful templates:

### 1. Response Template (`templates/response.html`)
- Gradient header design
- Query display section
- Formatted response content
- Metadata (model, timestamp)

### 2. CVE Card Template (`templates/cve_card.html`)
- Color-coded severity badges (Red/Orange/Yellow/Green)
- Large CVSS score display
- Exploit existence warnings
- CISA KEV indicators
- Detailed information grid
- Affected products section
- Solution recommendations

## 🛠️ Key Components

### MCP Server (`mcp_server.py`)
- 8 specialized tools with MCP decorators
- Direct MongoDB integration
- Handles tool routing based on LLM decisions

### LLM Agent (`agent.py`)
- Function agent capabilities (tool calling with GPT-4)
- MCP client capabilities (connects to MCP server)
- Intelligent query understanding and tool selection
- Iterative processing for complex queries

### Streamlit App (`streamlit_app.py`)
- Modern, responsive web interface
- Jinja2 template rendering
- Real-time query processing
- Visual CVE card display
- Query templates for easy use

### Tools Available

1. `query_cve_by_number` - Find specific CVE
2. `query_cve_by_severity` - Filter by CRITICAL/HIGH/MEDIUM/LOW
3. `query_cve_by_cvss_range` - Query by score range
4. `query_cve_by_keyword` - Full-text search
5. `query_cve_by_product` - Find by affected product
6. `query_cve_with_exploit` - Filter by exploit availability
7. `query_cve_by_cisa_key` - Find CISA KEV entries
8. `get_cve_statistics` - Aggregate statistics

## 🔍 How It Works

1. **User enters a query** in Streamlit or CLI
2. **Agent (GPT-4) analyzes** the query
3. **Tool selection** happens automatically
4. **MCP server** queries your MongoDB data
5. **Jinja2 templates** format the response beautifully
6. **Streamlit displays** professional CVE cards
7. **Multiple tools** can be chained automatically

## 📝 Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# Verify your database and collection exist
mongosh
> use your_database_name
> db.cve_details.countDocuments()
```

### Missing API Key
Make sure your `.env` file has a valid OpenAI API key:
```env
OPENAI_API_KEY=sk-...
```

### Import Errors
Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

### Streamlit Not Opening
Try running directly:
```bash
streamlit run streamlit_app.py
```

## 🎯 Next Steps

1. ✅ Configure your existing MongoDB connection
2. ✅ Add OpenAI API key
3. ✅ Run Streamlit interface
4. Customize Jinja2 templates for your needs
5. Add more tools to the MCP server
6. Integrate with other security tools
7. Deploy to production

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
