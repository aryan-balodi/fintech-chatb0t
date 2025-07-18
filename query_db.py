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

# Get user query and start retrieval
user_query = input("🔍 Enter your query: ")

print("🔄 Embedding user query...")
query_embedding = model.encode(user_query).tolist()
print("✅ Query embedded!\n")

print(f"🔄 Performing similarity search in ChromaDB...")
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5  # Adjust as desired
)
print("✅ Retrieval complete!\n")

print("🎯 Top Retrieved Chunks:\n")
for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    print(f"Result {i+1}:")
    print("Content:")
    print(doc)
    print("Metadata:", meta)
    print("-" * 80)
