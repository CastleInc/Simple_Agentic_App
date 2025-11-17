"""
MCP Server with MongoDB CVE query capabilities.
This server provides multiple tools using individual @app.tool() decorators
for different types of CVE queries based on user requests.
"""

import os
import json
from typing import Any, Dict
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp.types import TextContent

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "vulnerabilities")

# Initialize MongoDB client
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]
cve_collection = db["cve_details"]

# Initialize MCP Server with FastMCP
app = FastMCP("cve-query-server")


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to JSON-serializable format."""
    if doc is None:
        return {}

    serialized = {}
    for key, value in doc.items():
        if key == "_id":
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_mongo_doc(value)
        else:
            serialized[key] = value
    return serialized


# ============================================================================
# CVE Query Tools - Individual decorators for different query types
# ============================================================================

@app.tool()
async def query_cve_by_number(cve_number: str) -> list[TextContent]:
    """
    Query CVE details by CVE number (e.g., CVE-2020-000001).

    Args:
        cve_number: The CVE number to search for (e.g., CVE-2020-000001)

    Returns:
        Complete CVE information including severity, CVSS score, description, and remediation
    """
    try:
        result = cve_collection.find_one({"cve_number": cve_number})

        if result:
            serialized_result = serialize_mongo_doc(result)
            return [TextContent(
                type="text",
                text=json.dumps(serialized_result, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=f"No CVE found with number: {cve_number}"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE by number: {str(e)}"
        )]


@app.tool()
async def query_cve_by_severity(severity: str, limit: int = 10) -> list[TextContent]:
    """
    Query CVEs by severity level.

    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, or LOW)
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of CVEs matching the specified severity level
    """
    try:
        results = list(cve_collection.find(
            {"severity": severity.upper()}
        ).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "severity": severity,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE by severity: {str(e)}"
        )]


@app.tool()
async def query_cve_by_cvss_range(min_score: float, max_score: float, limit: int = 10) -> list[TextContent]:
    """
    Query CVEs by CVSS score range.

    Args:
        min_score: Minimum CVSS score (0.0-10.0)
        max_score: Maximum CVSS score (0.0-10.0)
        limit: Maximum number of results to return (default: 10)

    Returns:
        CVEs within the specified CVSS score range
    """
    try:
        results = list(cve_collection.find({
            "cvss_score": {"$gte": min_score, "$lte": max_score}
        }).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "min_score": min_score,
                "max_score": max_score,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE by CVSS range: {str(e)}"
        )]


@app.tool()
async def query_cve_by_keyword(keyword: str, limit: int = 10) -> list[TextContent]:
    """
    Search CVEs by keyword in title, description, or keywords field.

    Args:
        keyword: Keyword to search for in CVE details
        limit: Maximum number of results to return (default: 10)

    Returns:
        CVEs matching the search keyword
    """
    try:
        # Search in multiple fields
        results = list(cve_collection.find({
            "$or": [
                {"cve_title": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}},
                {"keywords": {"$regex": keyword, "$options": "i"}}
            ]
        }).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "keyword": keyword,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE by keyword: {str(e)}"
        )]


@app.tool()
async def query_cve_by_product(product_name: str, limit: int = 10) -> list[TextContent]:
    """
    Query CVEs by affected product name.

    Args:
        product_name: Product name to search for (e.g., 'Red Hat', 'Windows', 'Apache')
        limit: Maximum number of results to return (default: 10)

    Returns:
        CVEs affecting the specified product
    """
    try:
        results = list(cve_collection.find({
            "affected_products": {"$regex": product_name, "$options": "i"}
        }).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "product": product_name,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE by product: {str(e)}"
        )]


@app.tool()
async def query_cve_with_exploit(exploit_exists: bool = True, limit: int = 10) -> list[TextContent]:
    """
    Query CVEs that have known exploits.

    Args:
        exploit_exists: True to find CVEs with exploits, False for without (default: True)
        limit: Maximum number of results to return (default: 10)

    Returns:
        CVEs with or without known exploits
    """
    try:
        query_value = "Exploit Exists" if exploit_exists else {"$ne": "Exploit Exists"}
        results = list(cve_collection.find({
            "classifications_exploit": query_value
        }).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "exploit_exists": exploit_exists,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE with exploit: {str(e)}"
        )]


@app.tool()
async def query_cve_by_cisa_key(limit: int = 10) -> list[TextContent]:
    """
    Query CVEs that are marked as CISA KEV (Known Exploited Vulnerabilities).

    Args:
        limit: Maximum number of results to return (default: 10)

    Returns:
        CVEs marked as CISA Known Exploited Vulnerabilities
    """
    try:
        results = list(cve_collection.find({
            "cisa_key": "Yes"
        }).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CISA KEV CVEs: {str(e)}"
        )]


@app.tool()
async def get_cve_statistics() -> list[TextContent]:
    """
    Get statistical summary of CVE data.

    Returns:
        Statistics including counts by severity, average CVSS scores, exploit counts, etc.
    """
    try:
        # Aggregate statistics
        pipeline = [
            {
                "$group": {
                    "_id": "$severity",
                    "count": {"$sum": 1},
                    "avg_cvss": {"$avg": "$cvss_score"}
                }
            }
        ]

        severity_stats = list(cve_collection.aggregate(pipeline))
        total_count = cve_collection.count_documents({})

        stats = {
            "total_cves": total_count,
            "by_severity": severity_stats,
            "cisa_kev_count": cve_collection.count_documents({"cisa_key": "Yes"}),
            "with_exploits": cve_collection.count_documents({"classifications_exploit": "Exploit Exists"})
        }

        return [TextContent(
            type="text",
            text=json.dumps(stats, indent=2, default=str)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error getting CVE statistics: {str(e)}"
        )]


@app.tool()
async def query_cve_by_attack_type(attack_type: str, limit: int = 10) -> list[TextContent]:
    """
    Query CVEs by attack/exploitation type.

    Args:
        attack_type: Type of attack (e.g., 'Buffer Overflow', 'SQL Injection', 'XSS')
        limit: Maximum number of results to return (default: 10)

    Returns:
        CVEs with the specified attack type
    """
    try:
        results = list(cve_collection.find({
            "classifications_attack_type": {"$regex": attack_type, "$options": "i"}
        }).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "attack_type": attack_type,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying CVE by attack type: {str(e)}"
        )]


@app.tool()
async def query_recent_cves(days: int = 30, limit: int = 20) -> list[TextContent]:
    """
    Query recently modified or discovered CVEs.

    Args:
        days: Number of days to look back (default: 30)
        limit: Maximum number of results to return (default: 20)

    Returns:
        Recently modified CVEs within the specified timeframe
    """
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        results = list(cve_collection.find({
            "source_last_modified_date": {"$gte": cutoff_date}
        }).sort("source_last_modified_date", -1).limit(limit))

        serialized_results = [serialize_mongo_doc(doc) for doc in results]
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(serialized_results),
                "days_back": days,
                "results": serialized_results
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error querying recent CVEs: {str(e)}"
        )]


if __name__ == "__main__":
    app.run()