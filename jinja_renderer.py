"""
Jinja2 Template Renderer for CVE Data
Handles all template rendering logic separately from the main Streamlit app.
"""

import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any


class JinjaRenderer:
    """Handles all Jinja2 template rendering for CVE data and responses."""

    def __init__(self, template_dir='templates'):
        """Initialize the Jinja2 environment."""
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Add custom filters
        self.env.filters['format_severity_color'] = self.get_severity_color
        self.env.filters['format_cvss_color'] = self.get_cvss_color

    @staticmethod
    def get_severity_color(severity: str) -> str:
        """Get color based on severity level."""
        colors = {
            "CRITICAL": "#dc2626",
            "HIGH": "#ea580c",
            "MEDIUM": "#f59e0b",
            "LOW": "#84cc16"
        }
        return colors.get(severity, "#6b7280")

    @staticmethod
    def get_cvss_color(score: float) -> str:
        """Get color based on CVSS score."""
        if score >= 9.0:
            return "#dc2626"  # Critical
        elif score >= 7.0:
            return "#ea580c"  # High
        elif score >= 4.0:
            return "#f59e0b"  # Medium
        else:
            return "#84cc16"  # Low

    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response string."""
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            return {"type": "text", "content": response}

    def render_cve_card(self, cve_data: Dict[str, Any]) -> str:
        """
        Render a CVE card using the cve_card.html template.

        Args:
            cve_data: Dictionary containing CVE information

        Returns:
            Rendered HTML string
        """
        try:
            # Parse JSON if string
            if isinstance(cve_data, str):
                cve_data = json.loads(cve_data)

            template = self.env.get_template('cve_card.html')
            rendered = template.render(cve=cve_data)
            return rendered

        except Exception as e:
            return f"<div class='error-message'>Error formatting CVE data: {str(e)}</div>"

    def render_response(self, response: str) -> str:
        """
        Render the agent response with appropriate template.

        Args:
            response: The response string (JSON or text)

        Returns:
            Rendered HTML string
        """
        data = self.parse_response(response)

        if isinstance(data, dict):
            # Single CVE
            if "_id" in data and "cve_number" in data:
                return self.render_cve_card(data)

            # Statistics
            elif "total_cves" in data:
                return self.render_statistics(data)

            # Multiple CVEs
            elif "results" in data and isinstance(data["results"], list):
                return self.render_multiple_cves(data)

            # Plain text response
            elif "type" in data and data["type"] == "text":
                return f"<div class='response-text'>{data['content']}</div>"

        # Fallback
        return f'<pre style="background: #f3f4f6; padding: 15px; border-radius: 8px; overflow: auto;">{json.dumps(data, indent=2)}</pre>'

    def render_multiple_cves(self, data: Dict[str, Any]) -> str:
        """
        Render multiple CVE cards.

        Args:
            data: Dictionary with 'results' containing list of CVE data

        Returns:
            Combined HTML string of all CVE cards
        """
        try:
            template = self.env.get_template('cve_list.html')
            rendered = template.render(
                count=data.get('count', 0),
                severity=data.get('severity', ''),
                results=data.get('results', [])
            )
            return rendered
        except Exception as e:
            # Fallback to simple rendering
            html = f'<h3>Found {data.get("count", 0)} CVEs</h3>'
            for cve in data.get('results', []):
                html += self.render_cve_card(cve)
            return html

    def render_statistics(self, data: Dict[str, Any]) -> str:
        """
        Render CVE statistics using template.

        Args:
            data: Dictionary containing statistics data

        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.get_template('statistics.html')
            rendered = template.render(stats=data)
            return rendered
        except Exception as e:
            return f"<div class='error-message'>Error formatting statistics: {str(e)}</div>"
