import os
import sys
import json
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm

# Add the scripts directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from chunking import chunk_service_json, chunk_vendor_health_json


def list_json_files(root_folder):
    """Recursively get all JSON files under the root folder."""
    files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for fname in filenames:
            if fname.lower().endswith('.json'):
                files.append(os.path.join(dirpath, fname))
    return files


def get_relative_path(root_folder, abspath):
    """Get relative path to use in metadata and IDs."""
    return os.path.relpath(abspath, root_folder)


def main():
    # Get the project root directory (parent of scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    root_folder = os.path.join(project_root, 'knowledge_base')
    db_path = os.path.join(project_root, 'vector_db')

    print(f"Scanning for JSON files under: {root_folder}")
    json_files = list_json_files(root_folder)
    print(f"Found {len(json_files)} JSON files.")

    documents = []
    metadatas = []
    ids = []

    print("Processing and chunking JSON files...")
    for file_path in tqdm(json_files, desc="Processing JSON files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                service_json = json.load(f)
        except Exception as e:
            print(f"⚠️  Skipping {file_path} due to error: {e}")
            continue

        # Use special chunking for vendor health data
        if "vendor_health.json" in file_path:
            chunks = chunk_vendor_health_json(service_json)
        else:
            chunks = chunk_service_json(service_json)

        relative_path = get_relative_path(root_folder, file_path)
        for chunk in chunks:
            documents.append(chunk["content"])
            # Add file path in metadata for hierarchy preservation
            chunk_meta = chunk["metadata"].copy()
            chunk_meta["file_path"] = relative_path
            metadatas.append(chunk_meta)

            # Create unique ID: replace os separators for consistency in IDs
            clean_path = relative_path.replace(os.sep, "_")
            chunk_name_sanitized = chunk['chunk_name'].replace(' ', '_')
            unique_id = f"{clean_path}:{chunk_name_sanitized}"
            ids.append(unique_id)

    print(f"Total chunks prepared: {len(documents)}")

    print("Loading embedding model...")
    # BGE models are better for structured data and RAG applications
    model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    # Alternative: model = SentenceTransformer("BAAI/bge-large-en-v1.5") for better performance

    print("Generating embeddings for chunks...")
    embeddings = []
    for doc in tqdm(documents, desc="Embedding chunks"):
        emb = model.encode(doc)
        embeddings.append(emb.tolist())

    print("Connecting to ChromaDB and storing vectors...")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="fintech_services")

    # Clear existing collection to avoid duplicates when re-running
    try:
        collection.delete()
        collection = client.get_or_create_collection(name="fintech_services")
        print("✅ Cleared existing collection for fresh data.")
    except Exception as e:
        print(f"⚠️  Note: Could not clear collection (might be empty): {e}")

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )

    print(f"✅ Successfully embedded and stored {len(documents)} chunks in ChromaDB at '{db_path}'.")


if __name__ == "__main__":
    main()
