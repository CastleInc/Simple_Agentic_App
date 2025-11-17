# CVE Query Agent - Architecture & Flow Diagram

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Streamlit Web   │    │  CLI Interactive │                  │
│  │  Interface       │    │  Terminal        │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
└───────────┼──────────────────────┼─────────────────────────────┘
            │                      │
            └──────────┬───────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CVE AGENT (agent.py)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Ollama/OpenAI Client (configured via env)              │  │
│  │  • Tool Management & Routing                               │  │
│  │  • Conversation Loop Handler                               │  │
│  │  • System Prompt Manager                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │  MCP Client Session   │
                │  (stdio communication) │
                └───────────┬───────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MCP SERVER (mcp_server.py)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Tool Registry (10 CVE query tools):                       │  │
│  │  • query_cve_by_number                                     │  │
│  │  • query_cve_by_severity                                   │  │
│  │  • query_cve_by_cvss_range                                 │  │
│  │  • query_cve_by_keyword                                    │  │
│  │  • query_cve_by_product                                    │  │
│  │  • query_cve_with_exploit                                  │  │
│  │  • query_cve_by_cisa_key                                   │  │
│  │  • get_cve_statistics                                      │  │
│  │  • query_cve_by_attack_type                                │  │
│  │  • query_recent_cves                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MongoDB Database                              │
│  Database: genai_kb                                              │
│  Collection: cve_details                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CVE Documents with fields:                                │  │
│  │  • cve_number, severity, cvss_score                        │  │
│  │  • description, keywords, affected_products                │  │
│  │  • classifications_exploit, cisa_key                       │  │
│  │  • source_last_modified_date                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detailed Component Flow

### 1️⃣ **Application Startup Flow**

```
START (main.py or streamlit_app.py)
  │
  ├─→ Load Environment Variables (.env)
  │   ├─→ OPENAI_API_KEY=fake-key
  │   ├─→ OPENAI_BASE_URL=http://localhost:11434/v1
  │   ├─→ OPENAI_MODEL_NAME=llama3.2
  │   ├─→ MONGODB_URI=mongodb://localhost:27017/
  │   └─→ MCP_CVE_SERVER_ENABLED=true
  │
  ├─→ Initialize CVEAgent
  │   ├─→ Create OpenAI/Ollama client
  │   ├─→ Load system prompt (from prompts.py)
  │   └─→ Initialize empty tool registry
  │
  └─→ Enter Agent Context (__aenter__)
      │
      └─→ connect_to_mcp_servers()
          │
          ├─→ Read MCP Config (mcp_config.py)
          │   └─→ Get enabled servers from env
          │
          ├─→ For each enabled server:
          │   │
          │   ├─→ Create StdioServerParameters
          │   │   ├─→ command: "python"
          │   │   └─→ args: ["mcp_server.py"]
          │   │
          │   ├─→ Launch MCP Server Process (subprocess)
          │   │   │
          │   │   └─→ mcp_server.py starts
          │   │       ├─→ Initialize MongoDB connection
          │   │       ├─→ Create Server instance
          │   │       ├─→ Register @app.list_tools()
          │   │       ├─→ Register @app.call_tool()
          │   │       └─→ Start stdio_server loop
          │   │
          │   ├─→ Create stdio_client
          │   ├─→ Create ClientSession
          │   ├─→ session.initialize()
          │   │
          │   └─→ session.list_tools()
          │       │
          │       └─→ Receive 10 tool definitions
          │           └─→ Convert to OpenAI function format
          │
          └─→ Store tools in self.available_tools[]

READY TO PROCESS QUERIES
```

---

### 2️⃣ **Query Processing Flow**

```
USER SUBMITS QUERY: "Show me critical CVEs"
  │
  ▼
agent.chat(user_query)
  │
  ├─→ Build messages array:
  │   ├─→ [0] system: system_prompt
  │   └─→ [1] user: "Show me critical CVEs"
  │
  ├─→ Convert tools to OpenAI format
  │
  └─→ ITERATION LOOP (max 5 iterations)
      │
      ├─→ Call Ollama API
      │   │
      │   └─→ POST http://localhost:11434/v1/chat/completions
      │       ├─→ model: "llama3.2"
      │       ├─→ messages: [system, user]
      │       └─→ tools: [10 available tools]
      │
      ├─→ Ollama/LLM Analyzes Query
      │   │
      │   └─→ Decision: Need to call tool
      │       └─→ Returns: tool_call for "query_cve_by_severity"
      │           └─→ arguments: {"severity": "CRITICAL", "limit": 10}
      │
      ├─→ Agent Processes Tool Call
      │   │
      │   ├─→ Find server that provides tool (cve)
      │   │
      │   ├─→ session.call_tool()
      │   │   │
      │   │   └─→ Send to MCP Server via stdio
      │   │       │
      │   │       └─→ MCP Server receives call
      │   │           │
      │   │           ├─→ Route to query_cve_by_severity()
      │   │           │
      │   │           ├─→ Execute MongoDB Query:
      │   │           │   db.cve_details.find(
      │   │           │     {"severity": "CRITICAL"}
      │   │           │   ).limit(10)
      │   │           │
      │   │           ├─→ Serialize results
      │   │           │
      │   │           └─→ Return TextContent with JSON
      │   │
      │   └─→ Store tool result
      │
      ├─→ Append tool result to messages
      │   │
      │   └─→ messages array now:
      │       ├─→ [0] system
      │       ├─→ [1] user: "Show me critical CVEs"
      │       ├─→ [2] assistant: tool_call
      │       └─→ [3] tool: {result JSON}
      │
      ├─→ Call Ollama API AGAIN (next iteration)
      │   │
      │   └─→ LLM synthesizes final answer
      │       └─→ finish_reason: "stop"
      │           └─→ Returns natural language response
      │
      └─→ Return (response_text, tool_results)
```

---

### 3️⃣ **Response Rendering Flow (Streamlit)**

```
Agent returns (response, tool_results)
  │
  ├─→ streamlit_app.py receives response
  │
  ├─→ JinjaRenderer.render()
  │   │
  │   ├─→ Parse tool_results
  │   │
  │   ├─→ Determine result type:
  │   │   ├─→ Single CVE → use cve_card.html template
  │   │   └─→ Multiple CVEs → use response.html template
  │   │
  │   └─→ Render HTML with Jinja2
  │       ├─→ Apply custom CSS (styles.py)
  │       └─→ Format CVE data beautifully
  │
  └─→ st.markdown(rendered_html, unsafe_allow_html=True)
      │
      └─→ Display in browser
```

---

## 🔄 Complete Execution Sequence Diagram

```
┌─────────┐     ┌──────────┐     ┌───────────┐     ┌────────────┐
│  User   │     │ Streamlit│     │ CVEAgent  │     │ MCP Server │     ┌─────────┐
│         │     │   App    │     │           │     │            │     │ MongoDB │
└────┬────┘     └────┬─────┘     └─────┬─────┘     └─────┬──────┘     └────┬────┘
     │               │                  │                  │                 │
     │ 1. Start App  │                  │                  │                 │
     │──────────────>│                  │                  │                 │
     │               │                  │                  │                 │
     │               │ 2. Initialize    │                  │                 │
     │               │    Agent         │                  │                 │
     │               │─────────────────>│                  │                 │
     │               │                  │                  │                 │
     │               │                  │ 3. Connect to    │                 │
     │               │                  │    MCP Server    │                 │
     │               │                  │─────────────────>│                 │
     │               │                  │                  │                 │
     │               │                  │                  │ 4. Connect to   │
     │               │                  │                  │    MongoDB      │
     │               │                  │                  │────────────────>│
     │               │                  │                  │                 │
     │               │                  │ 5. list_tools()  │                 │
     │               │                  │<─────────────────│                 │
     │               │                  │                  │                 │
     │               │ 6. Ready         │                  │                 │
     │               │<─────────────────│                  │                 │
     │               │                  │                  │                 │
     │ 7. Enter Query│                  │                  │                 │
     │──────────────>│                  │                  │                 │
     │               │                  │                  │                 │
     │               │ 8. chat(query)   │                  │                 │
     │               │─────────────────>│                  │                 │
     │               │                  │                  │                 │
     │               │                  │ 9. Call Ollama   │                 │
     │               │                  │    API           │                 │
     │               │                  │ (localhost:11434)│                 │
     │               │                  │                  │                 │
     │               │                  │ 10. LLM decides  │                 │
     │               │                  │     tool to call │                 │
     │               │                  │                  │                 │
     │               │                  │ 11. call_tool()  │                 │
     │               │                  │─────────────────>│                 │
     │               │                  │                  │                 │
     │               │                  │                  │ 12. Query DB    │
     │               │                  │                  │────────────────>│
     │               │                  │                  │                 │
     │               │                  │                  │ 13. Results     │
     │               │                  │                  │<────────────────│
     │               │                  │                  │                 │
     │               │                  │ 14. Tool result  │                 │
     │               │                  │<─────────────────│                 │
     │               │                  │                  │                 │
     │               │                  │ 15. Call Ollama  │                 │
     │               │                  │     again with   │                 │
     │               │                  │     tool result  │                 │
     │               │                  │                  │                 │
     │               │                  │ 16. Final answer │                 │
     │               │                  │                  │                 │
     │               │ 17. Response +   │                  │                 │
     │               │     tool_results │                  │                 │
     │               │<─────────────────│                  │                 │
     │               │                  │                  │                 │
     │               │ 18. Render with  │                  │                 │
     │               │     Jinja2       │                  │                 │
     │               │                  │                  │                 │
     │ 19. Display   │                  │                  │                 │
     │    Results    │                  │                  │                 │
     │<──────────────│                  │                  │                 │
```

---

## 🔧 Key Configuration Files

### **.env** - Environment Configuration
- **OPENAI_API_KEY**: `fake-key` (Ollama doesn't validate)
- **OPENAI_BASE_URL**: `http://localhost:11434/v1` (Ollama endpoint)
- **OPENAI_MODEL_NAME**: `llama3.2` (or any Ollama model)
- **MONGODB_URI**: MongoDB connection string
- **MCP_CVE_SERVER_ENABLED**: Enables/disables MCP server

### **prompts.py** - System Prompts
- Defines agent behavior
- Controls how LLM interprets queries
- Guides tool selection logic

### **mcp_config.py** - MCP Configuration
- Reads MCP server settings from env
- Manages multiple server connections
- Provides server discovery

---

## 🚀 How to Run

### Option 1: Interactive CLI
```bash
python agent.py
```

### Option 2: Streamlit Web Interface
```bash
streamlit run streamlit_app.py
```

### Option 3: Via main.py
```bash
python main.py              # Interactive mode
python main.py --streamlit  # Web interface
```

---

## 📊 Tool Routing Logic

When LLM receives a query, it analyzes and selects the appropriate tool:

| Query Pattern | Selected Tool | MongoDB Query |
|---------------|---------------|---------------|
| "CVE-2020-0001" | `query_cve_by_number` | `{cve_number: "CVE-2020-0001"}` |
| "critical CVEs" | `query_cve_by_severity` | `{severity: "CRITICAL"}` |
| "CVSS > 9" | `query_cve_by_cvss_range` | `{cvss_score: {$gte: 9.0}}` |
| "SQL injection" | `query_cve_by_keyword` | `{$or: [{description: /SQL/i}]}` |
| "Red Hat" | `query_cve_by_product` | `{affected_products: /Red Hat/i}` |
| "with exploits" | `query_cve_with_exploit` | `{classifications_exploit: "Exploit Exists"}` |
| "CISA KEV" | `query_cve_by_cisa_key` | `{cisa_key: "Yes"}` |
| "statistics" | `get_cve_statistics` | Aggregation pipeline |
| "buffer overflow" | `query_cve_by_attack_type` | `{classifications_attack_type: /buffer/i}` |
| "recent CVEs" | `query_recent_cves` | `{source_last_modified_date: {$gte: date}}` |

---

## 🛠️ Troubleshooting

### Issue: "Connection closed" error
**Cause**: MCP server not starting properly
**Solution**: Check that `stdio_server` is imported in mcp_server.py ✅ (FIXED)

### Issue: "No tools loaded"
**Cause**: MCP server crashed during tool registration
**Solution**: Ensure MongoDB is running and accessible

### Issue: Ollama connection error
**Cause**: Ollama not running or wrong port
**Solution**: 
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/v1/models
```

---

## 📝 Summary

This system uses a **3-tier architecture**:
1. **UI Layer**: Streamlit/CLI
2. **Agent Layer**: LLM-powered reasoning with tool routing
3. **Data Layer**: MCP Server → MongoDB

The **Ollama configuration** allows you to run everything locally without external API calls, using `fake-key` as the API key since Ollama doesn't require authentication.

