import json
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chunking import chunk_service_json
from tqdm import tqdm  # Import tqdm

# Load JSON service
with open('PAN_ADVANCED.json', 'r') as f:
    service_json = json.load(f)

# Chunk the JSON
chunks = chunk_service_json(service_json)
print(f"Chunking complete: {len(chunks)} chunks generated.")

# Prepare lists for Chroma
documents = []
metadatas = []
ids = []

# Add progress bar for chunk preparation
for chunk in tqdm(chunks, desc="Preparing chunks"):
    documents.append(chunk["content"])
    metadatas.append(chunk["metadata"])
    ids.append(f"{chunk['metadata']['service_name']}_{chunk['chunk_name'].replace(' ', '_')}")

# Initialize embedding model
model = SentenceTransformer("all-mpnet-base-v2")

# Embed chunks with progress bar
embeddings = []
for doc in tqdm(documents, desc="Embedding chunks"):
    emb = model.encode(doc)
    embeddings.append(emb.tolist())

# Set up ChromaDB
db_path = "./vector_db"
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(name="fintech_services")

# Add chunks to ChromaDB
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids,
    embeddings=embeddings
)

print(f"✅ {len(documents)} chunks embedded and stored in ChromaDB at '{db_path}'!")
