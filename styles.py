"""
CSS Styles for Streamlit CVE Query Application
Centralized styling for better maintainability.
"""


def get_custom_css():
    """Return all custom CSS styles as a string."""
    return """
    <style>
        /* Main Header Styles */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        
        /* Button Styles */
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 5px;
            font-weight: 600;
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Stat Card Styles */
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }
        
        /* CVE Card Styles */
        .cve-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        
        .cve-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .cve-number {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .severity-badge {
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            text-transform: uppercase;
        }
        
        .cvss-score {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 15px 0;
        }
        
        .cvss-number {
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .cve-title {
            font-size: 20px;
            color: #34495e;
            margin: 15px 0;
            font-weight: 600;
            line-height: 1.4;
        }
        
        .cve-description {
            color: #555;
            line-height: 1.8;
            margin: 20px 0;
            font-size: 16px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .cve-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .detail-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }
        
        .detail-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }
        
        .detail-value {
            font-weight: 600;
            color: #2c3e50;
            font-size: 15px;
        }
        
        .affected-products {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            line-height: 1.6;
        }
        
        .solution {
            background: #d4edda;
            border: 2px solid #28a745;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            line-height: 1.6;
        }
        
        .exploit-warning {
            background: #f8d7da;
            border: 2px solid #dc3545;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        .cisa-warning {
            background: #d1ecf1;
            border: 2px solid #0c5460;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .error-message {
            color: #dc3545;
            background: #f8d7da;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #dc3545;
            margin: 10px 0;
        }
        
        /* Response Container */
        .response-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 0;
        }
        
        .response-content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 0 0 10px 10px;
            border: 1px solid #e0e0e0;
        }
        
        .query-text {
            background: white;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        
        .answer-text {
            background: white;
            padding: 20px;
            border-radius: 5px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
    """

