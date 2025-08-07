#!/usr/bin/env python3
"""
Script to test Pinecone connection and setup.
Run this first to ensure Pinecone is configured correctly.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pinecone_connection():
    """Test Pinecone connection and setup"""
    try:
        from pinecone import Pinecone, ServerlessSpec
        
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENVIRONMENT", "")
        index_name = os.getenv("PINECONE_INDEX_NAME", "chatscribe-documents")
        
        if not api_key:
            print("❌ PINECONE_API_KEY not found in environment variables")
            print("   Please add your Pinecone API key to the .env file")
            return False
        
        if api_key == "your-pinecone-api-key-here":
            print("❌ Please replace 'your-pinecone-api-key-here' with your actual Pinecone API key")
            return False
            
        print(f"🔑 Using API key: {api_key[:20]}...")
        print(f"📍 Index name: {index_name}")
        
        # Initialize Pinecone
        print("🔄 Connecting to Pinecone...")
        pc = Pinecone(api_key=api_key)
        
        # List existing indexes
        print("📋 Checking existing indexes...")
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
        print(f"   Found {len(existing_indexes)} indexes: {existing_indexes}")
        
        # Create index if it doesn't exist
        if index_name not in existing_indexes:
            print(f"🆕 Creating new index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            print(f"✅ Successfully created index: {index_name}")
        else:
            print(f"✅ Index already exists: {index_name}")
        
        # Connect to index
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        print(f"📊 Index stats:")
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        print(f"   Namespaces: {len(stats.get('namespaces', {}))}")
        
        if stats.get('namespaces'):
            for namespace, ns_stats in stats['namespaces'].items():
                print(f"     - {namespace}: {ns_stats['vector_count']} vectors")
        
        print("🎉 Pinecone connection test successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please install pinecone-client: pip install pinecone-client")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("   Please check your Pinecone API key and network connection")
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            return False
        
        print(f"🔑 Using OpenAI API key: {api_key[:20]}...")
        
        # Test embedding
        from langchain.embeddings.openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        test_text = "This is a test"
        result = embeddings.embed_query(test_text)
        
        print(f"✅ OpenAI embeddings working (dimension: {len(result)})")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Pinecone and OpenAI connections...\n")
    
    print("1. Testing OpenAI connection:")
    openai_ok = test_openai_connection()
    
    print("\n2. Testing Pinecone connection:")
    pinecone_ok = test_pinecone_connection()
    
    print(f"\n{'='*50}")
    if openai_ok and pinecone_ok:
        print("🎉 All tests passed! You can now run the document reprocessing.")
        print("   Run: python3 reprocess_documents.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        if not openai_ok:
            print("   - Fix OpenAI API key configuration")
        if not pinecone_ok:
            print("   - Fix Pinecone API key configuration")
