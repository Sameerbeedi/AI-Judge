"""
Vector Database Service using Qdrant
Handles semantic similarity search for cases and arguments
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict, Optional
import hashlib

class VectorDBService:
    def __init__(self):
        # Initialize Qdrant client
        qdrant_url = os.getenv("QDRANT_URL", ":memory:")  # In-memory for local dev
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        
        if qdrant_url == ":memory:":
            self.client = QdrantClient(":memory:")
            self.use_cloud = False
        else:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            self.use_cloud = True
        
        # Initialize embedding model (384 dimensions)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # Collection names
        self.cases_collection = "cases"
        self.arguments_collection = "arguments"
        
        # Initialize collections
        self._init_collections()
    
    def _init_collections(self):
        """Initialize Qdrant collections"""
        try:
            # Cases collection
            if not self.client.collection_exists(self.cases_collection):
                self.client.create_collection(
                    collection_name=self.cases_collection,
                    vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
                )
                print(f"✅ Created collection: {self.cases_collection}")
            
            # Arguments collection
            if not self.client.collection_exists(self.arguments_collection):
                self.client.create_collection(
                    collection_name=self.arguments_collection,
                    vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
                )
                print(f"✅ Created collection: {self.arguments_collection}")
        except Exception as e:
            print(f"⚠️  Qdrant initialization error: {e}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def index_case(self, case_id: str, side_a_text: str, side_b_text: str, verdict: str = ""):
        """Index a complete case for semantic search"""
        try:
            # Combine all case information
            case_text = f"Case ID: {case_id}\n\nSide A: {side_a_text}\n\nSide B: {side_b_text}"
            if verdict:
                case_text += f"\n\nVerdict: {verdict}"
            
            # Generate embedding
            embedding = self._generate_embedding(case_text)
            
            # Store in Qdrant
            point = PointStruct(
                id=self._generate_id(case_id),
                vector=embedding,
                payload={
                    "case_id": case_id,
                    "side_a_text": side_a_text[:500],  # Store preview
                    "side_b_text": side_b_text[:500],
                    "verdict": verdict[:500] if verdict else "",
                    "indexed_at": str(datetime.utcnow())
                }
            )
            
            self.client.upsert(
                collection_name=self.cases_collection,
                points=[point]
            )
            
            print(f"✅ Indexed case: {case_id}")
            return True
        except Exception as e:
            print(f"❌ Error indexing case {case_id}: {e}")
            return False
    
    def index_argument(self, case_id: str, side: str, argument_text: str, argument_type: str = "initial"):
        """Index an individual argument"""
        try:
            # Generate embedding
            embedding = self._generate_embedding(argument_text)
            
            # Generate unique ID
            arg_id = self._generate_id(f"{case_id}_{side}_{argument_type}_{argument_text[:50]}")
            
            # Store in Qdrant
            point = PointStruct(
                id=arg_id,
                vector=embedding,
                payload={
                    "case_id": case_id,
                    "side": side,
                    "argument_text": argument_text[:1000],
                    "argument_type": argument_type,
                    "indexed_at": str(datetime.utcnow())
                }
            )
            
            self.client.upsert(
                collection_name=self.arguments_collection,
                points=[point]
            )
            
            return True
        except Exception as e:
            print(f"❌ Error indexing argument: {e}")
            return False
    
    def find_similar_cases(self, query_text: str, limit: int = 5, min_score: float = 0.7) -> List[Dict]:
        """Find similar cases using semantic search"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query_text)
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.cases_collection,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=min_score
            )
            
            # Format results
            similar_cases = []
            for result in results:
                similar_cases.append({
                    "case_id": result.payload["case_id"],
                    "similarity_score": round(result.score, 4),
                    "side_a_preview": result.payload["side_a_text"],
                    "side_b_preview": result.payload["side_b_text"],
                    "verdict_preview": result.payload.get("verdict", "")
                })
            
            return similar_cases
        except Exception as e:
            print(f"❌ Error searching cases: {e}")
            return []
    
    def find_similar_arguments(self, query_text: str, side: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Find similar arguments across all cases"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query_text)
            
            # Build filter
            filter_conditions = None
            if side:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                filter_conditions = Filter(
                    must=[FieldCondition(key="side", match=MatchValue(value=side))]
                )
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.arguments_collection,
                query_vector=query_embedding,
                query_filter=filter_conditions,
                limit=limit,
                score_threshold=0.65
            )
            
            # Format results
            similar_args = []
            for result in results:
                similar_args.append({
                    "case_id": result.payload["case_id"],
                    "side": result.payload["side"],
                    "argument": result.payload["argument_text"],
                    "similarity_score": round(result.score, 4),
                    "argument_type": result.payload.get("argument_type", "initial")
                })
            
            return similar_args
        except Exception as e:
            print(f"❌ Error searching arguments: {e}")
            return []
    
    def find_winning_patterns(self, winning_side: str, limit: int = 20) -> List[Dict]:
        """Find common patterns in winning arguments"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Get all winning arguments for the side
            filter_conditions = Filter(
                must=[FieldCondition(key="side", match=MatchValue(value=winning_side))]
            )
            
            # This is a placeholder - in production, you'd track which arguments won
            # For now, we'll return high-performing arguments
            results = self.client.scroll(
                collection_name=self.arguments_collection,
                scroll_filter=filter_conditions,
                limit=limit
            )
            
            patterns = []
            for point in results[0]:
                patterns.append({
                    "case_id": point.payload["case_id"],
                    "argument": point.payload["argument_text"],
                    "side": point.payload["side"]
                })
            
            return patterns
        except Exception as e:
            print(f"❌ Error finding patterns: {e}")
            return []
    
    def get_case_recommendations(self, case_id: str, side_a_text: str, side_b_text: str, limit: int = 5) -> Dict:
        """Get comprehensive recommendations for a case"""
        try:
            # Combine case text
            case_text = f"Side A: {side_a_text}\n\nSide B: {side_b_text}"
            
            # Find similar cases
            similar_cases = self.find_similar_cases(case_text, limit=limit)
            
            # Find similar arguments for each side
            similar_side_a = self.find_similar_arguments(side_a_text, side="A", limit=3)
            similar_side_b = self.find_similar_arguments(side_b_text, side="B", limit=3)
            
            return {
                "similar_cases": similar_cases,
                "similar_arguments": {
                    "side_a": similar_side_a,
                    "side_b": similar_side_b
                },
                "recommendations": self._generate_recommendations(similar_cases, similar_side_a, similar_side_b)
            }
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, similar_cases, similar_a, similar_b) -> List[str]:
        """Generate text recommendations based on similar cases"""
        recommendations = []
        
        if similar_cases:
            recommendations.append(f"Found {len(similar_cases)} similar cases in the database")
        
        if similar_a:
            recommendations.append(f"Side A's arguments are similar to {len(similar_a)} previous arguments")
        
        if similar_b:
            recommendations.append(f"Side B's arguments are similar to {len(similar_b)} previous arguments")
        
        if not recommendations:
            recommendations.append("This appears to be a unique case with no close precedents")
        
        return recommendations
    
    def delete_case(self, case_id: str):
        """Delete a case and its arguments from vector DB"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Delete from cases collection
            case_point_id = self._generate_id(case_id)
            self.client.delete(
                collection_name=self.cases_collection,
                points_selector=[case_point_id]
            )
            
            # Delete all arguments for this case
            filter_conditions = Filter(
                must=[FieldCondition(key="case_id", match=MatchValue(value=case_id))]
            )
            self.client.delete(
                collection_name=self.arguments_collection,
                points_selector=filter_conditions
            )
            
            return True
        except Exception as e:
            print(f"❌ Error deleting case from vector DB: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get vector database statistics"""
        try:
            cases_info = self.client.get_collection(self.cases_collection)
            args_info = self.client.get_collection(self.arguments_collection)
            
            return {
                "total_cases_indexed": cases_info.points_count,
                "total_arguments_indexed": args_info.points_count,
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dimension": self.embedding_dim,
                "distance_metric": "cosine",
                "status": "connected"
            }
        except Exception as e:
            return {"error": str(e), "status": "disconnected"}
    
    def check_connection(self) -> bool:
        """Check if Qdrant is available"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            print(f"Qdrant connection check failed: {e}")
            return False


# Global instance
from datetime import datetime
vector_db = VectorDBService()
