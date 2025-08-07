#!/usr/bin/env python3
"""
Comprehensive connection test for ChatScribe2
Tests all required services and APIs
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_database_connection():
    """Test PostgreSQL database connection"""
    print("🗄️  Testing Database Connection...")
    try:
        # Test direct psycopg2 connection
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='chatscribe2',
            user='postgres',
            password='Steves0705'
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        print(f"   ✅ PostgreSQL connection successful")
        print(f"   📍 Version: {version.split(',')[0]}")
        
        # Check tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   📊 Tables found: {', '.join(tables)}")
        
        # Check document count
        if 'documents' in tables:
            cursor.execute('SELECT COUNT(*) FROM documents;')
            doc_count = cursor.fetchone()[0]
            print(f"   📄 Documents in database: {doc_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy ORM connection"""
    print("\n🔗 Testing SQLAlchemy ORM...")
    try:
        from app.core.config import settings
        from app.core.database import get_db
        
        # Test the actual ORM connection
        db = next(get_db())
        
        # Try to query something
        from sqlalchemy import text
        
        result = db.execute(text("SELECT 1 as test")).fetchone()
        if result and result[0] == 1:
            print("   ✅ SQLAlchemy ORM connection successful")
            
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ SQLAlchemy connection failed: {e}")
        return False

def test_alternative_ai_service():
    """Test Alternative AI Service (SentenceTransformers + Ollama/SimpleLLM)"""
    print("\n🤖 Testing Alternative AI Service...")
    try:
        from app.core.alternative_ai_service import alternative_ai_service
        
        # Test embeddings
        try:
            test_text = "This is a test sentence."
            embedding = alternative_ai_service.embeddings.embed_query(test_text)
            if embedding and len(embedding) == 384:  # all-MiniLM-L6-v2 dimension
                print("   ✅ SentenceTransformer embeddings working (384 dimensions)")
                embeddings_ok = True
            else:
                print(f"   ❌ Embeddings issue: got {len(embedding) if embedding else 0} dimensions")
                embeddings_ok = False
        except Exception as e:
            print(f"   ❌ Embeddings error: {e}")
            embeddings_ok = False
        
        # Test LLM
        try:
            test_response = alternative_ai_service.llm("Hello, this is a test.")
            if test_response and len(test_response.strip()) > 0:
                llm_type = alternative_ai_service.llm._llm_type
                print(f"   ✅ LLM working (Type: {llm_type})")
                llm_ok = True
            else:
                print("   ❌ LLM returned empty response")
                llm_ok = False
        except Exception as e:
            print(f"   ❌ LLM error: {e}")
            llm_ok = False
        
        return embeddings_ok and llm_ok
        
    except Exception as e:
        print(f"   ❌ Alternative AI Service error: {e}")
        return False

def test_pinecone_connection():
    """Test Pinecone API connection"""
    print("\n🌲 Testing Pinecone API...")
    try:
        from app.core.config import settings
        
        if not settings.PINECONE_API_KEY:
            print("   ❌ No Pinecone API key configured")
            return False
            
        print(f"   🔑 Using API key: {settings.PINECONE_API_KEY[:15]}...")
        print(f"   📍 Index name: {settings.PINECONE_INDEX_NAME}")
        
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # List indexes
        indexes = [index_info["name"] for index_info in pc.list_indexes()]
        print(f"   📋 Available indexes: {', '.join(indexes)}")
        
        # Check if our index exists
        if settings.PINECONE_INDEX_NAME in indexes:
            print(f"   ✅ Index '{settings.PINECONE_INDEX_NAME}' exists")
            
            # Get index stats
            index = pc.Index(settings.PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            namespaces = stats.get('namespaces', {})
            
            print(f"   📊 Total vectors: {total_vectors}")
            print(f"   📁 Namespaces: {len(namespaces)}")
            
            for namespace, data in namespaces.items():
                vector_count = data.get('vector_count', 0)
                print(f"      - {namespace}: {vector_count} vectors")
        else:
            print(f"   ⚠️  Index '{settings.PINECONE_INDEX_NAME}' not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pinecone API error: {e}")
        return False

def test_file_upload_directory():
    """Test file upload directory"""
    print("\n📁 Testing File Upload Directory...")
    try:
        from app.core.config import settings
        
        upload_dir = settings.UPLOAD_DIR
        print(f"   📍 Upload directory: {upload_dir}")
        
        if not os.path.exists(upload_dir):
            print(f"   ⚠️  Upload directory doesn't exist, creating it...")
            os.makedirs(upload_dir, exist_ok=True)
        
        # Check if we can write to it
        test_file = os.path.join(upload_dir, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("   ✅ Upload directory is writable")
        except Exception as e:
            print(f"   ❌ Upload directory not writable: {e}")
            return False
        
        # Count existing files
        files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
        print(f"   📄 Existing uploaded files: {len(files)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ File upload directory error: {e}")
        return False

def main():
    """Run all connection tests"""
    print("🧪 ChatScribe2 - Comprehensive Connection Test")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_sqlalchemy_connection,
        test_alternative_ai_service,
        test_pinecone_connection,
        test_file_upload_directory
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY:")
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Database Connection",
        "SQLAlchemy ORM", 
        "Alternative AI Service",
        "Pinecone API",
        "File Upload Directory"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some systems need attention. Check the API keys in your .env file.")

if __name__ == "__main__":
    main()
