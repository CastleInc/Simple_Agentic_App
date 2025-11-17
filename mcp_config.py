"""
MCP Server Configuration Manager
Loads and manages multiple MCP server configurations from environment variables.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class MCPConfig:
    """Manages MCP server configurations from environment variables."""

    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_servers()

    def _load_servers(self):
        """Load all enabled MCP servers from environment variables."""
        # Get all environment variables
        env_vars = os.environ

        # Find all MCP server prefixes
        server_prefixes = set()
        for key in env_vars.keys():
            if key.startswith("MCP_") and key.endswith("_SERVER_ENABLED"):
                # Extract server name (e.g., MCP_CVE_SERVER_ENABLED -> CVE)
                prefix = key.replace("MCP_", "").replace("_SERVER_ENABLED", "")
                server_prefixes.add(prefix)

        # Load configuration for each enabled server
        for prefix in server_prefixes:
            enabled = os.getenv(f"MCP_{prefix}_SERVER_ENABLED", "false").lower() == "true"

            if enabled:
                command = os.getenv(f"MCP_{prefix}_SERVER_COMMAND", "python")
                args_str = os.getenv(f"MCP_{prefix}_SERVER_ARGS", "")
                description = os.getenv(f"MCP_{prefix}_SERVER_DESCRIPTION", "")

                # Parse args (support comma-separated or space-separated)
                args = [arg.strip() for arg in args_str.split() if arg.strip()]

                # Create server config
                server_name = prefix.lower()
                self.servers[server_name] = MCPServerConfig(
                    name=server_name,
                    command=command,
                    args=args,
                    env=None,  # Can be extended to support custom env vars
                    description=description or f"{prefix} MCP Server"
                )

        print(f"📡 Loaded {len(self.servers)} MCP server(s): {', '.join(self.servers.keys())}")

    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of all enabled server configurations."""
        return list(self.servers.values())

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific server."""
        return self.servers.get(name.lower())

    def has_servers(self) -> bool:
        """Check if any servers are configured."""
        return len(self.servers) > 0


# Global configuration instance
mcp_config = MCPConfig()

