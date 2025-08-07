import os
import openai
import hashlib
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from pinecone import Pinecone, ServerlessSpec
from .config import settings

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY


class AIService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        
        # Initialize Pinecone
        self.pc = None
        self.index = None
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        try:
            if not settings.PINECONE_API_KEY:
                print("Warning: PINECONE_API_KEY not found in environment")
                return
                
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, create if not
            index_name = settings.PINECONE_INDEX_NAME
            existing_indexes = [index_info["name"] for index_info in self.pc.list_indexes()]
            
            if index_name not in existing_indexes:
                print(f"Creating Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=1024,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            
            self.index = self.pc.Index(index_name)
            print(f"Connected to Pinecone index: {index_name}")
            
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
    
    def _get_document_namespace(self, document_id: int) -> str:
        """Generate namespace for document in Pinecone"""
        return f"doc_{document_id}"
    
    def process_document_content(self, content: str, document_id: int) -> Optional[PineconeVectorStore]:
        """Process document content and create vector store in Pinecone"""
        try:
            if not self.index:
                print("Pinecone not initialized")
                return None
            
            # Split text into chunks
            texts = self.text_splitter.split_text(content)
            
            # Create namespace for this document
            namespace = self._get_document_namespace(document_id)
            
            # Delete existing vectors for this document (if any)
            try:
                self.index.delete(delete_all=True, namespace=namespace)
            except:
                pass  # Ignore if namespace doesn't exist
            
            # Create vector store and add texts
            vectorstore = PineconeVectorStore.from_texts(
                texts=texts,
                embedding=self.embeddings,
                index_name=settings.PINECONE_INDEX_NAME,
                namespace=namespace,
                pinecone_api_key=settings.PINECONE_API_KEY
            )
            
            print(f"Successfully processed document {document_id} into Pinecone")
            return vectorstore
            
        except Exception as e:
            print(f"Error processing document: {e}")
            return None
    
    def load_vectorstore(self, document_id: int) -> Optional[PineconeVectorStore]:
        """Load existing vectorstore for a document from Pinecone"""
        try:
            if not self.index:
                print("Pinecone not initialized")
                return None
            
            namespace = self._get_document_namespace(document_id)
            
            # Check if namespace has any vectors
            stats = self.index.describe_index_stats()
            if namespace not in stats.get('namespaces', {}):
                print(f"No vectors found for document {document_id}")
                return None
            
            # Create vectorstore instance
            vectorstore = PineconeVectorStore(
                index=self.index,
                embedding=self.embeddings,
                namespace=namespace
            )
            
            return vectorstore
            
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
            return None
    
    def create_conversation_chain(self, vectorstore: PineconeVectorStore, chat_history: List[tuple]) -> ConversationalRetrievalChain:
        """Create conversation chain with memory"""
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Load existing chat history into memory
        for human_msg, ai_msg in chat_history:
            if human_msg:
                memory.chat_memory.add_user_message(human_msg)
            if ai_msg:
                memory.chat_memory.add_ai_message(ai_msg)
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(),
            memory=memory,
            return_source_documents=True
        )
        
        return qa_chain
    
    def chat_with_document(self, 
                          document_id: int, 
                          question: str, 
                          chat_history: List[tuple] = None) -> str:
        """Chat with a document using Q&A"""
        try:
            # Load vectorstore
            vectorstore = self.load_vectorstore(document_id)
            if not vectorstore:
                return "Error: Document not processed or vectorstore not found. Please reprocess the document."
            
            # Create conversation chain
            if chat_history is None:
                chat_history = []
            
            qa_chain = self.create_conversation_chain(vectorstore, chat_history)
            
            # Get response
            result = qa_chain({"question": question})
            return result["answer"]
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return "I'm sorry, I encountered an error while processing your question."
    
    def summarize_document(self, content: str) -> str:
        """Summarize document content"""
        try:
            # Split content if too long
            max_tokens = 3000  # Leave room for prompt and response
            if len(content) > max_tokens:
                # Take first portion for summary
                content = content[:max_tokens]
            
            prompt = f"""
            Please provide a comprehensive summary of the following document:
            
            {content}
            
            Summary:
            """
            
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].text.strip()
            
        except Exception as e:
            print(f"Error in summarization: {e}")
            return "Error generating summary."
    
    def get_chat_title(self, first_message: str) -> str:
        """Generate a title for the chat session based on the first message"""
        try:
            # Keep it simple - use first few words or generate with AI
            words = first_message.split()[:5]
            title = " ".join(words)
            if len(title) > 50:
                title = title[:47] + "..."
            return title or "New Chat"
        except:
            return "New Chat"


# Global AI service instance
ai_service = AIService()
