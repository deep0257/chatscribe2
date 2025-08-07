#!/usr/bin/env python3
"""
Script to reprocess existing documents and create vectorstores for chat functionality.
This fixes the "document not found or vectorstore not found" error.
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db
from app.crud.crud import get_user_documents
from app.core.alternative_ai_service import alternative_ai_service as ai_service
from app.models.models import User, Document


def reprocess_all_documents():
    """Reprocess all documents to create vectorstores"""
    db = next(get_db())
    
    try:
        # Get all documents from database
        all_documents = db.query(Document).all()
        
        if not all_documents:
            print("No documents found in database.")
            return
            
        print(f"Found {len(all_documents)} documents to process...")
        
        processed_count = 0
        failed_count = 0
        
        for document in all_documents:
            print(f"\nProcessing document ID {document.id}: {document.original_filename}")
            
            if not document.content:
                print(f"  ⚠️  Skipping - no content available")
                failed_count += 1
                continue
                
            try:
                # Create vectorstore for this document
                vectorstore = ai_service.process_document_content(document.content, document.id)
                
                if vectorstore:
                    print(f"  ✅ Successfully created vectorstore for document {document.id}")
                    processed_count += 1
                else:
                    print(f"  ❌ Failed to create vectorstore for document {document.id}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing document {document.id}: {e}")
                failed_count += 1
        
        print(f"\n🎉 Processing complete!")
        print(f"   Successfully processed: {processed_count}")
        print(f"   Failed: {failed_count}")
        print(f"   Total: {len(all_documents)}")
        
        # Verify vectorstores were created in Pinecone
        try:
            if ai_service.index:
                stats = ai_service.index.describe_index_stats()
                namespaces = stats.get('namespaces', {})
                print(f"\n📁 Pinecone index contains {len(namespaces)} document namespaces:")
                for namespace in namespaces:
                    vector_count = namespaces[namespace]['vector_count']
                    print(f"   - {namespace}: {vector_count} vectors")
            else:
                print("\n⚠️  Pinecone not initialized - check your API keys")
        except Exception as e:
            print(f"\n❌ Error checking Pinecone stats: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Starting document reprocessing...")
    reprocess_all_documents()
