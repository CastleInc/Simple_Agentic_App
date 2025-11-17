#!/usr/bin/env python3
"""
Ollama Diagnostic Script
Tests if Ollama is working properly with your CVE Agent setup
"""

import os
import sys
import requests
import json
from openai import OpenAI

print("=" * 70)
print("🔍 Ollama Diagnostic Test")
print("=" * 70)

# Test 1: Check if Ollama API is accessible
print("\n[1/5] Testing Ollama API accessibility...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        print("✅ Ollama API is accessible")
        data = response.json()
        models = data.get("models", [])
        print(f"   Found {len(models)} model(s):")
        for model in models:
            print(f"   - {model['name']} ({model['details']['parameter_size']})")
    else:
        print(f"❌ Ollama API returned status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Cannot connect to Ollama: {e}")
    print("\n💡 Solution: Start Ollama with 'ollama serve'")
    sys.exit(1)

# Test 2: Check OpenAI-compatible endpoint
print("\n[2/5] Testing OpenAI-compatible endpoint...")
try:
    response = requests.get("http://localhost:11434/v1/models", timeout=5)
    if response.status_code == 200:
        print("✅ OpenAI-compatible endpoint is working")
    else:
        print(f"⚠️  OpenAI endpoint returned status {response.status_code}")
except Exception as e:
    print(f"❌ OpenAI endpoint error: {e}")

# Test 3: Check .env configuration
print("\n[3/5] Checking .env configuration...")
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model_name = os.getenv("LLM_MODEL_NAME")

print(f"   API Key: {api_key}")
print(f"   Base URL: {base_url}")
print(f"   Model: {model_name}")

if api_key == "fake-key" and "11434" in base_url:
    print("✅ Configuration looks correct for Ollama")
else:
    print("⚠️  Configuration might need adjustment")

# Test 4: Test OpenAI client with Ollama
print("\n[4/5] Testing LLM client with Ollama...")
try:
    client = OpenAI(
        api_key=api_key or "fake-key",
        base_url=base_url or "http://localhost:11434/v1"
    )

    print(f"   Sending test message to {model_name}...")
    print("   (This may take 10-30 seconds on first run)")

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": "Reply with just: OK"}
        ],
        max_tokens=10,
        temperature=0
    )

    reply = response.choices[0].message.content
    print(f"✅ Ollama responded: '{reply}'")

except Exception as e:
    print(f"❌ OpenAI client error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check MongoDB connection
print("\n[5/5] Testing MongoDB connection...")
try:
    from pymongo import MongoClient

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    mongo_db = os.getenv("MONGODB_DATABASE", "genai_kb")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    db = client[mongo_db]

    # Try to access the database
    client.server_info()

    # Check if CVE collection exists
    collections = db.list_collection_names()
    if "cve_details" in collections:
        count = db.cve_details.count_documents({})
        print(f"✅ MongoDB connected - {count} CVE documents found")
    else:
        print(f"⚠️  MongoDB connected but 'cve_details' collection not found")
        print(f"   Available collections: {collections}")

except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    print("   The agent will not work without MongoDB!")

# Summary
print("\n" + "=" * 70)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 70)
print("\n✅ = Working | ⚠️  = Needs attention | ❌ = Not working\n")
print("Next steps:")
print("  1. If all tests passed, run: python agent.py")
print("  2. If Ollama test failed, wait a moment and try again")
print("  3. If MongoDB failed, ensure MongoDB is running")
print("\n" + "=" * 70)
