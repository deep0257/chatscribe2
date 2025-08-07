import os
import requests
import numpy as np
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pinecone import Pinecone, ServerlessSpec
from .config import settings

# Try to import SentenceTransformer with error handling
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SentenceTransformers not available: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    
# Try to import torch with error handling
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class SentenceTransformerEmbeddings(Embeddings):
    """Custom Langchain embeddings using SentenceTransformers"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        embedding = self.model.encode([text])
        return embedding[0].tolist()


class OllamaLLM(LLM):
    """Custom Ollama LLM for Langchain"""
    
    model: str = "llama3.2:1b"
    base_url: str = "http://localhost:11434"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> str:
        """Call Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running on localhost:11434"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @property
    def _llm_type(self) -> str:
        return "ollama"


class SimpleLLM(LLM):
    """Simple fallback LLM that provides basic responses"""
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> str:
        """Simple rule-based responses"""
        # Extract context from prompt (this is a simple implementation)
        if "context:" in prompt.lower():
            lines = prompt.split('\n')
            context_lines = []
            in_context = False
            
            for line in lines:
                if "context:" in line.lower():
                    in_context = True
                    continue
                elif "question:" in line.lower():
                    in_context = False
                    question = line.split(':', 1)[1].strip()
                    break
                elif in_context:
                    context_lines.append(line.strip())
            
            if context_lines:
                context = ' '.join(context_lines[:3])  # Use first 3 lines
                return f"Based on the document context: {context}"
            
        return "I can help you with questions about the uploaded document. The document processing system is working with basic text analysis."
    
    @property
    def _llm_type(self) -> str:
        return "simple"


class AlternativeAIService:
    def __init__(self):
        # Initialize embeddings
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embeddings = SentenceTransformerEmbeddings('all-MiniLM-L6-v2')
                print("✅ SentenceTransformer embeddings initialized")
            except Exception as e:
                print(f"⚠️  SentenceTransformer failed: {e}")
                self.embeddings = None
        else:
            print("⚠️  SentenceTransformers not available, embeddings disabled")
            self.embeddings = None
        
        # Try Ollama first, fallback to SimpleLLM
        try:
            self.llm = OllamaLLM()
            # Test the connection
            test_response = self.llm("test")
            if "Error: Cannot connect" in test_response:
                raise Exception("Ollama not available")
            print("✅ Connected to Ollama LLM (llama3.2:1b)")
        except:
            print("⚠️  Ollama not available, using SimpleLLM fallback")
            self.llm = SimpleLLM()
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Initialize Pinecone
        self.pc = None
        self.index = None
        self._initialize_pinecone()

    def _initialize_pinecone(self):
        try:
            if not settings.PINECONE_API_KEY:
                print("Warning: PINECONE_API_KEY not found in environment")
                return
                
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            index_name = settings.PINECONE_INDEX_NAME
            existing_indexes = [index_info["name"] for index_info in self.pc.list_indexes()]

            # Check if index exists with wrong dimension and delete it
            if index_name in existing_indexes:
                # Check the dimension of existing index
                index_info = self.pc.describe_index(index_name)
                existing_dimension = index_info.dimension
                
                if existing_dimension != 384:
                    print(f"🔄 Existing index has dimension {existing_dimension}, but we need 384. Recreating...")
                    print(f"⚠️  This will delete all existing vectors in the index!")
                    
                    # Delete the existing index
                    self.pc.delete_index(index_name)
                    print(f"🗑️  Deleted existing index: {index_name}")
                    
                    # Wait a moment for deletion to complete
                    import time
                    time.sleep(5)
                    
                    # Create new index with correct dimension
                    print(f"🔨 Creating new Pinecone index: {index_name} (384 dimensions)")
                    self.pc.create_index(
                        name=index_name,
                        dimension=384,  # Output dimension of embedding model
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud='aws',
                            region='us-east-1'
                        )
                    )
                else:
                    print(f"✅ Existing index has correct dimension: {existing_dimension}")
            else:
                print(f"🔨 Creating Pinecone index: {index_name} (384 dimensions)")
                self.pc.create_index(
                    name=index_name,
                    dimension=384,  # Output dimension of embedding model
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

    def process_document_content(self, content: str, document_id: int) -> Optional[bool]:
        """Process document content and create vectors in Pinecone"""
        try:
            if not self.index or not self.embeddings:
                print("Pinecone or embeddings not initialized")
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
            
            # Create embeddings for all texts
            embeddings = self.embeddings.embed_documents(texts)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                vectors.append({
                    "id": f"doc_{document_id}_chunk_{i}",
                    "values": embedding,
                    "metadata": {"text": text, "document_id": document_id}
                })
            
            # Upload vectors to Pinecone
            self.index.upsert(vectors=vectors, namespace=namespace)
            
            print(f"Successfully processed document {document_id} into Pinecone ({len(vectors)} chunks)")
            return True
            
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
            
            # Simple approach: search for relevant content and use SimpleLLM
            # Get relevant documents
            docs = vectorstore.similarity_search(question, k=3)
            
            if not docs:
                return "I couldn't find relevant information in the document to answer your question."
            
            # Combine relevant text
            context = "\n".join([doc.page_content for doc in docs])
            
            # Create a prompt for the LLM
            prompt = f"""Based on the following context from the document, please answer the question.

Context:
{context}

Question: {question}

Answer:"""
            
            # Get response from LLM
            response = self.llm(prompt)
            return response.strip() if response else "I'm sorry, I couldn't generate a response based on the document content."
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return "I'm sorry, I encountered an error while processing your question."
    
    def summarize_document(self, content: str) -> str:
        """Summarize document content"""
        try:
            # Split content if too long
            max_chars = 2000  # Keep it reasonable for the LLM
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
            
            prompt = f"""Please provide a comprehensive summary of the following document:
            
{content}

Summary:"""
            
            summary = self.llm(prompt)
            return summary.strip() if summary else "Unable to generate summary."
            
        except Exception as e:
            print(f"Error in summarization: {e}")
            return "Error generating summary."
    
    def get_chat_title(self, first_message: str) -> str:
        """Generate a title for the chat session based on the first message"""
        try:
            # Keep it simple - use first few words
            words = first_message.split()[:5]
            title = " ".join(words)
            if len(title) > 50:
                title = title[:47] + "..."
            return title or "New Chat"
        except:
            return "New Chat"

# Global instance
alternative_ai_service = AlternativeAIService()
