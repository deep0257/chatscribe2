#!/usr/bin/env python3
"""
Test script to check document processing without making OpenAI API calls.
This helps isolate the problem.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_openai_quota():
    """Test if OpenAI quota is working"""
    try:
        from langchain.embeddings.openai import OpenAIEmbeddings
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False, "No OpenAI API key found"
        
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        # Try a simple test
        result = embeddings.embed_query("test")
        return True, f"OpenAI working (dimension: {len(result)})"
        
    except Exception as e:
        return False, str(e)

def test_document_retrieval():
    """Test retrieving documents from database"""
    try:
        from app.core.database import get_db
        from app.models.models import Document
        
        db = next(get_db())
        documents = db.query(Document).all()
        db.close()
        
        return len(documents), [{"id": doc.id, "filename": doc.original_filename, "has_content": bool(doc.content)} for doc in documents]
        
    except Exception as e:
        return 0, str(e)

def test_pinecone_connection():
    """Test Pinecone connection"""
    try:
        from pinecone import Pinecone
        
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "chatscribe2")
        
        if not api_key:
            return False, "No Pinecone API key found"
        
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        return True, stats
        
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    print("🧪 Testing document processing components...\n")
    
    # Test 1: Document retrieval
    print("1. Testing document retrieval from database:")
    doc_count, doc_info = test_document_retrieval()
    if isinstance(doc_info, list):
        print(f"   ✅ Found {doc_count} documents:")
        for doc in doc_info:
            status = "✅ Has content" if doc["has_content"] else "❌ No content"
            print(f"      - ID {doc['id']}: {doc['filename']} ({status})")
    else:
        print(f"   ❌ Error: {doc_info}")
    
    # Test 2: Pinecone connection
    print("\n2. Testing Pinecone connection:")
    pinecone_ok, pinecone_result = test_pinecone_connection()
    if pinecone_ok:
        print("   ✅ Pinecone connected successfully")
        print(f"      Total vectors: {pinecone_result.get('total_vector_count', 0)}")
        print(f"      Namespaces: {len(pinecone_result.get('namespaces', {}))}")
        if pinecone_result.get('namespaces'):
            for ns, stats in pinecone_result['namespaces'].items():
                print(f"         - {ns}: {stats['vector_count']} vectors")
    else:
        print(f"   ❌ Pinecone error: {pinecone_result}")
    
    # Test 3: OpenAI quota
    print("\n3. Testing OpenAI API quota:")
    openai_ok, openai_result = test_openai_quota()
    if openai_ok:
        print(f"   ✅ {openai_result}")
    else:
        print(f"   ❌ OpenAI error: {openai_result}")
    
    print(f"\n{'='*60}")
    
    if not openai_ok:
        print("❌ MAIN ISSUE: OpenAI API quota exceeded")
        print("   SOLUTION: You need to:")
        print("   1. Add credits to your OpenAI account")
        print("   2. Or get a new API key with available quota")
        print("   3. Update the OPENAI_API_KEY in your .env file")
        print()
        print("   Without a working OpenAI API key, document processing")
        print("   (which requires embeddings) will not work.")
    elif not pinecone_ok:
        print("❌ ISSUE: Pinecone not connected properly")
        print("   Check your Pinecone API key and index configuration")
    elif doc_count == 0:
        print("❌ ISSUE: No documents found in database")
        print("   Upload some documents first")
    else:
        print("🎉 All components look good!")
        print("   The issue is likely that documents haven't been processed yet.")
        print("   You need to fix the OpenAI quota issue first, then run:")
        print("   python3 reprocess_documents.py")
