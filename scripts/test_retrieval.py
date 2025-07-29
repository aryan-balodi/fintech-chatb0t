#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_db import get_relevant_chunks
from sentence_transformers import SentenceTransformer
import chromadb

def test_retrieval():
    """Test what data we're actually retrieving from the vector database."""
    
    print("🔄 Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    print("✅ Model loaded!")
    
    print("\n🔄 Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="./vector_db")
    collection = client.get_or_create_collection(name="fintech_services")
    print("✅ Connected to ChromaDB!")
    
    # Test queries
    test_queries = [
        "vendor health metrics",
        "AzureRaven performance",
        "vendor success rate",
        "PAN_ADVANCED service",
        "KYC/AML services",
        "vendor latency metrics"
    ]
    
    print("\n" + "="*60)
    print("TESTING VECTOR DATABASE RETRIEVAL")
    print("="*60)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 40)
        
        try:
            # Get chunks using the same method as main.py
            chunks_result = get_relevant_chunks(query, top_k=3)
            
            if not chunks_result or not chunks_result.get("documents"):
                print("❌ No chunks retrieved!")
                continue
            
            documents = chunks_result.get("documents", [])
            metadatas = chunks_result.get("metadatas", [])
            
            print(f"✅ Retrieved {len(documents)} chunks:")
            
            for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                print(f"\n--- Chunk {i+1} ---")
                print(f"Metadata: {metadata}")
                print(f"Content: {doc[:200]}...")  # First 200 chars
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_retrieval() 