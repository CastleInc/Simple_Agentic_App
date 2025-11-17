"""
System Prompts for CVE Query Agent
Configurable prompts for different agent behaviors.
"""

# Default system prompt for CVE security analyst agent
DEFAULT_SYSTEM_PROMPT = """You are a CVE security analyst. Your job is to query the CVE database and provide vulnerability information.

When a user asks about CVEs:
1. Use the available tools to query the database immediately
2. Present the results clearly
3. Highlight important fields like severity, CVSS score, and exploit status

Always query first, explain later. Accept any CVE format the user provides."""


# Concise prompt for quick queries
CONCISE_SYSTEM_PROMPT = """You are a CVE analyst. Query the database using available tools and present results clearly."""


def get_system_prompt(prompt_type: str = "default") -> str:
    """
    Get system prompt by type.

    Args:
        prompt_type: Type of prompt (default, concise)

    Returns:
        System prompt string
    """
    prompts = {
        "default": DEFAULT_SYSTEM_PROMPT,
        "concise": CONCISE_SYSTEM_PROMPT
    }

    return prompts.get(prompt_type, DEFAULT_SYSTEM_PROMPT)
