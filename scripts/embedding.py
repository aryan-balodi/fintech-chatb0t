import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm
from chunking import chunk_service_json  # Your chunking function/module


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
    root_folder = './knowledge_base'  # Update path as needed

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
    model = SentenceTransformer("all-mpnet-base-v2")

    print("Generating embeddings for chunks...")
    embeddings = []
    for doc in tqdm(documents, desc="Embedding chunks"):
        emb = model.encode(doc)
        embeddings.append(emb.tolist())

    print("Connecting to ChromaDB and storing vectors...")
    db_path = "./vector_db"
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="fintech_services")

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )

    print(f"✅ Successfully embedded and stored {len(documents)} chunks in ChromaDB at '{db_path}'.")


if __name__ == "__main__":
    main()
