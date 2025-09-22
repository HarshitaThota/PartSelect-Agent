"""
Vector Search Tool
Provides semantic search capabilities using Pinecone + OpenAI embeddings
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI

class VectorSearchTool:
    """Tool for semantic search using Pinecone and OpenAI embeddings"""

    def __init__(self, parts_data: List[Dict]):
        self.parts_data = parts_data
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "partselect-parts")

        # Initialize clients
        self.pc = None
        self.index = None
        self.openai_client = None

        # Only initialize if API keys are available
        if self.pinecone_api_key and self.pinecone_api_key != "your_pinecone_key_here":
            try:
                self.pc = Pinecone(api_key=self.pinecone_api_key)
                self.index = self.pc.Index(self.index_name)
                print(f"Connected to Pinecone index: {self.index_name}")
            except Exception as e:
                print(f"⚠️ Pinecone connection failed: {e}")

        if self.openai_api_key and self.openai_api_key != "your_openai_key_here":
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                print("Connected to OpenAI API")
            except Exception as e:
                print(f"⚠️ OpenAI connection failed: {e}")

    def is_available(self) -> bool:
        """Check if vector search is available"""
        return self.pc is not None and self.openai_client is not None

    async def create_embeddings(self, text: str) -> Optional[List[float]]:
        """Create embeddings using OpenAI text-embedding-3-small"""
        if not self.openai_client:
            return None

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float",
                dimensions=512  # Match Pinecone index dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            return None

    def _create_part_text(self, part: Dict) -> str:
        """Create searchable text representation of a part"""
        text_parts = [
            part.get("name", ""),
            part.get("brand", ""),
            part.get("category", ""),
            part.get("description", ""),
            part.get("partselect_number", ""),
            " ".join(part.get("compatible_models", [])),
            " ".join(part.get("keywords", []))
        ]
        return " ".join(filter(None, text_parts))

    async def initialize_index(self) -> bool:
        """Initialize the Pinecone index with parts data"""
        if not self.is_available():
            print("⚠️ Vector search not available - missing API keys")
            return False

        try:
            # Check if index exists
            try:
                index_stats = self.index.describe_index_stats()
                vector_count = index_stats.get('total_vector_count', 0)

                if vector_count > 0:
                    print(f"Index already initialized with {vector_count} vectors")
                    return True
            except:
                pass

            print("Initializing Pinecone index with parts data...")

            # Prepare vectors for upsert
            vectors_to_upsert = []
            batch_size = 100

            for i, part in enumerate(self.parts_data):
                part_text = self._create_part_text(part)
                embedding = await self.create_embeddings(part_text)

                if embedding:
                    vectors_to_upsert.append({
                        "id": part["partselect_number"],
                        "values": embedding,
                        "metadata": {
                            "name": part.get("name", ""),
                            "brand": part.get("brand", ""),
                            "category": part.get("category", ""),
                            "price": part.get("price", 0),
                            "in_stock": part.get("in_stock", True),
                            "appliance_type": part.get("appliance_type", ""),
                            "text": part_text[:1000]  # Truncate for metadata limits
                        }
                    })

                    # Batch upsert
                    if len(vectors_to_upsert) >= batch_size:
                        self.index.upsert(vectors=vectors_to_upsert)
                        print(f"📤 Uploaded batch {i//batch_size + 1}")
                        vectors_to_upsert = []

            # Upload remaining vectors
            if vectors_to_upsert:
                self.index.upsert(vectors=vectors_to_upsert)
                print("📤 Uploaded final batch")

            print(f"Successfully initialized index with {len(self.parts_data)} parts")
            return True

        except Exception as e:
            print(f"Error initializing index: {e}")
            return False

    async def semantic_search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Perform semantic search for parts"""
        if not self.is_available():
            return []

        try:
            # Create query embedding
            query_embedding = await self.create_embeddings(query)
            if not query_embedding:
                return []

            # Build filter for Pinecone
            pinecone_filter = {}
            if filters:
                if filters.get("appliance_type"):
                    pinecone_filter["appliance_type"] = {"$eq": filters["appliance_type"]}
                if filters.get("brand"):
                    pinecone_filter["brand"] = {"$eq": filters["brand"]}
                if filters.get("in_stock_only"):
                    pinecone_filter["in_stock"] = {"$eq": True}

            # Search in Pinecone
            search_params = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": True
            }
            if pinecone_filter:
                search_params["filter"] = pinecone_filter

            results = self.index.query(**search_params)

            # Convert to parts format
            found_parts = []
            for match in results.matches:
                # Find full part data
                part_number = match.id
                full_part = next((p for p in self.parts_data if p["partselect_number"] == part_number), None)

                if full_part:
                    # Add semantic score
                    part_with_score = full_part.copy()
                    part_with_score["semantic_score"] = match.score
                    part_with_score["search_type"] = "semantic"
                    found_parts.append(part_with_score)

            print(f"🔍 Semantic search for '{query}' found {len(found_parts)} results")
            return found_parts

        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

    async def hybrid_search(self, query: str, traditional_results: List[Dict], top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Combine traditional and semantic search results"""
        if not self.is_available():
            return traditional_results

        # Get semantic results with filters
        semantic_results = await self.semantic_search(query, top_k, filters)

        # Merge results, avoiding duplicates
        seen_parts = set()
        hybrid_results = []

        # Add traditional results first (they're usually more precise)
        for part in traditional_results:
            part_number = part["partselect_number"]
            if part_number not in seen_parts:
                part_copy = part.copy()
                part_copy["search_type"] = "traditional"
                hybrid_results.append(part_copy)
                seen_parts.add(part_number)

        # Add semantic results that aren't already included
        for part in semantic_results:
            part_number = part["partselect_number"]
            if part_number not in seen_parts:
                hybrid_results.append(part)
                seen_parts.add(part_number)

        # Limit to top_k results
        return hybrid_results[:top_k]

    async def find_similar_parts(self, part_number: str, top_k: int = 3) -> List[Dict]:
        """Find parts similar to a given part"""
        if not self.is_available():
            return []

        # Find the reference part
        reference_part = next((p for p in self.parts_data if p["partselect_number"] == part_number), None)
        if not reference_part:
            return []

        # Use the part's text for similarity search
        part_text = self._create_part_text(reference_part)
        similar_parts = await self.semantic_search(part_text, top_k + 1)  # +1 to exclude self

        # Remove the reference part from results
        return [p for p in similar_parts if p["partselect_number"] != part_number][:top_k]