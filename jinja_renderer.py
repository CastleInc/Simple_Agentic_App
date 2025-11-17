"""
Jinja2 Template Renderer for CVE Data
Handles all template rendering logic separately from the main Streamlit app.
"""

import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class JinjaRenderer:
    """Handles all Jinja2 template rendering for CVE data and responses."""

    def __init__(self, template_dir='templates'):
        """Initialize the Jinja2 environment."""
        self.env = Environment(loader=FileSystemLoader(template_dir))

    @staticmethod
    def get_severity_color(severity):
        """Get color based on severity level."""
        colors = {
            "CRITICAL": "#dc3545",
            "HIGH": "#fd7e14",
            "MEDIUM": "#ffc107",
            "LOW": "#28a745"
        }
        return colors.get(severity, "#6c757d")

    def render_cve_card(self, cve_data):
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

            # Prepare template variables
            severity = cve_data.get('severity', 'UNKNOWN')

            rendered = template.render(
                cve_number=cve_data.get('cve_number', 'N/A'),
                cve_title=cve_data.get('cve_title', 'No title available'),
                severity=severity,
                severity_color=self.get_severity_color(severity),
                cvss_score=cve_data.get('cvss_score', 'N/A'),
                description=cve_data.get('description', 'No description available'),
                exploit_exists=cve_data.get('classifications_exploit') == 'Exploit Exists',
                cisa_key=cve_data.get('cisa_key') == 'Yes',
                attack_type=cve_data.get('classifications_attack_type', 'N/A'),
                location=cve_data.get('classifications_location', 'N/A'),
                impact=cve_data.get('classifications_impact', 'N/A'),
                remediation_level=cve_data.get('remediation_level', 'N/A'),
                affected_products=cve_data.get('affected_products', 'N/A'),
                solution=cve_data.get('solution', 'N/A')
            )

            return rendered

        except Exception as e:
            return f"<div class='error-message'>Error formatting CVE data: {str(e)}</div>"

    def render_response(self, query, response, model="gpt-4o"):
        """
        Render a general response using the response.html template.

        Args:
            query: The user's query
            response: The response text
            model: The model name

        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.get_template('response.html')

            rendered = template.render(
                query=query,
                response=response,
                model=model,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            return rendered

        except Exception as e:
            return f"<div class='error-message'>Error formatting response: {str(e)}</div>"

    def render_multiple_cves(self, cve_list):
        """
        Render multiple CVE cards.

        Args:
            cve_list: List of CVE data dictionaries

        Returns:
            Combined HTML string of all CVE cards
        """
        html_parts = []
        for cve in cve_list:
            html_parts.append(self.render_cve_card(cve))

        return "\n".join(html_parts)

