import chromadb
import os
from sentence_transformers import SentenceTransformer


print("🔄 Loading embedding model into memory...")
# BGE models are better for structured data and RAG applications
model = SentenceTransformer("BAAI/bge-base-en-v1.5")
# Alternative: model = SentenceTransformer("BAAI/bge-large-en-v1.5") for better performance
print("✅ Embedding model loaded!\n")


print("🔄 Connecting to Chroma vector database (persistent on disk)...")
# Get the project root directory (parent of scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
db_path = os.path.join(project_root, 'vector_db')
client = chromadb.PersistentClient(path=db_path)
print("✅ Chroma vector database loaded into memory!\n")


print('🔄 Loading "fintech_services" collection...')
collection = client.get_or_create_collection(name="fintech_services")
print('✅ Collection "fintech_services" ready!\n')


def get_relevant_chunks(query: str, top_k: int = 5, category_filter: str = None) -> dict:
    """
    Retrieves the top-k relevant chunks from your vector database based on the user query.
    
    Args:
        query: The search query
        top_k: Number of chunks to retrieve
        category_filter: Optional category to filter by

    Returns:
        dict with keys:
            "documents": list of chunk texts,
            "metadatas": list of corresponding chunk metadata dicts
    """
    print(f"\n🔍 Retrieving {top_k} chunks for query: {query}")
    if category_filter:
        print(f"🔍 Filtering by category: {category_filter}")

    embedding = model.encode(query).tolist()

    # Build where clause for category filtering
    where_clause = None
    if category_filter:
        where_clause = {"category": category_filter}

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where_clause if where_clause else None
    )

    documents = results.get("documents", [[]])[0]  # List[str]
    metadatas = results.get("metadatas", [[]])[0]  # List[dict]

    return {
        "documents": documents,
        "metadatas": metadatas
    }
