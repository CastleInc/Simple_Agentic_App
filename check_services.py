#!/usr/bin/env python3
"""
Quick test script to verify all services are working
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_mongodb():
    """Check MongoDB connection"""
    try:
        from pymongo import MongoClient
        client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"), serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ MongoDB: Connected successfully")

        # Check database
        db = client[os.getenv("MONGODB_DATABASE", "genai_kb")]
        cve_count = db["cve_details"].count_documents({})
        print(f"   📊 Found {cve_count} CVE documents in database")
        return True
    except Exception as e:
        print(f"❌ MongoDB: Failed to connect - {e}")
        return False

def check_ollama():
    """Check Ollama connection"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama: Connected successfully")
            print(f"   🤖 Available models: {', '.join([m['name'] for m in models]) if models else 'None'}")

            # Check if llama3.1 is available
            has_llama = any('llama3.1' in m['name'] for m in models)
            if not has_llama:
                print(f"   ⚠️  Warning: llama3.1 model not found. Run: ollama pull llama3.1")
            return True
        else:
            print(f"❌ Ollama: Unexpected response - {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama: Failed to connect - {e}")
        print(f"   💡 Make sure Ollama is running: ollama serve")
        return False

def main():
    print("=" * 60)
    print("CVE Query Agent - Service Check")
    print("=" * 60)
    print()

    mongo_ok = check_mongodb()
    print()
    ollama_ok = check_ollama()
    print()

    if mongo_ok and ollama_ok:
        print("🎉 All services are ready! You can start the application.")
        print()
        print("To run the Streamlit app:")
        print("  ./run_app.sh")
        print()
        print("Or manually:")
        print("  python -m streamlit run streamlit_app.py")
        return 0
    else:
        print("❌ Some services are not ready. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

