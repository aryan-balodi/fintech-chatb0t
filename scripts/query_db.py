import chromadb
from sentence_transformers import SentenceTransformer


print("🔄 Loading embedding model into memory...")
model = SentenceTransformer("all-mpnet-base-v2")
print("✅ Embedding model loaded!\n")


print("🔄 Connecting to Chroma vector database (persistent on disk)...")
client = chromadb.PersistentClient(path="./vector_db")
print("✅ Chroma vector database loaded into memory!\n")


print('🔄 Loading "fintech_services" collection...')
collection = client.get_or_create_collection(name="fintech_services")
print('✅ Collection "fintech_services" ready!\n')


def get_relevant_chunks(query: str, top_k: int = 5) -> dict:
    """
    Retrieves the top-k relevant chunks from your vector database based on the user query.

    Returns:
        dict with keys:
            "documents": list of chunk texts,
            "metadatas": list of corresponding chunk metadata dicts
    """
    print(f"\n🔍 Retrieving {top_k} chunks for query: {query}")

    embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]  # List[str]
    metadatas = results.get("metadatas", [[]])[0]  # List[dict]

    return {
        "documents": documents,
        "metadatas": metadatas
    }
