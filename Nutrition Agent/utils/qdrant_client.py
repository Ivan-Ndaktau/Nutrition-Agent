import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Try to import Qdrant, fallback to mock if not available
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("Warning: Qdrant package not available. Using mock database.")

class QdrantNutritionDB:
    def __init__(self):
        if QDRANT_AVAILABLE:
            try:
                # Try to connect to Qdrant server
                qdrant_url = os.getenv("QDRANT_URL")
                qdrant_api_key = os.getenv("QDRANT_API_KEY")
                
                if qdrant_url and qdrant_api_key:
                    self.client = QdrantClient(
                        url=qdrant_url,
                        api_key=qdrant_api_key,
                        timeout=30
                    )
                    print("Success: Connected to Qdrant Cloud")
                else:
                    print("Using Qdrant in-memory mode")
                    self.client = QdrantClient(":memory:")
                    
            except Exception as e:
                print(f"Failed to connect to Qdrant: {e}")
                print("Falling back to in-memory mode")
                self.client = QdrantClient(":memory:")
        else:
            self.client = None
            print("Using mock database (Qdrant not available)")
        
        # --- PERUBAHAN PENTING DI SINI ---
        # Kita ganti nama collection agar membuat wadah baru yang bersih
        self.collection_name = "nutrition_data_gemini_v1" 
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize collection if it doesn't exist"""
        if not self.client:
            return
            
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    # --- GANTI UKURAN VEKTOR JADI 768 (Sesuai Gemini) ---
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
                print(f"Created new collection: {self.collection_name}")
        except Exception as e:
            print(f"Warning: Could not initialize collection: {e}")
    
    def store_nutrition_data(self, user_id: str, data: dict, embedding: List[float]):
        """Store user nutrition data with embeddings"""
        if not self.client:
            return
            
        try:
            point = PointStruct(
                id=user_id,
                vector=embedding,
                payload={
                    "user_id": user_id,
                    "nutrition_data": data,
                    "timestamp": data.get("calculated_at", "")
                }
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        except Exception as e:
            print(f"Warning: Could not store data: {e}")
    
    def search_similar_profiles(self, embedding: List[float], limit: int = 5):
        """Search for similar nutrition profiles"""
        if not self.client:
            return []
            
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit
            )
            return search_result
        except Exception as e:
            print(f"Warning: Could not search profiles: {e}")
            return []
    
    def get_user_data(self, user_id: str):
        """Retrieve specific user data"""
        if not self.client:
            return None
            
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[user_id]
            )
            return points[0] if points else None
        except Exception as e:
            print(f"Warning: Could not retrieve user data: {e}")
            return None