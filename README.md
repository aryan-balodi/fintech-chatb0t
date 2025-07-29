# Fintech Services Chatbot Platform

## Overview
This project is an interactive, retrieval-augmented chatbot platform for helping users select and evaluate fintech services and vendors. It leverages a vector database (ChromaDB), sentence-transformer embeddings, and a multi-stage conversational flow to guide users through category, service, and vendor selection, with recommendations based on real vendor health metrics.

## Features
- Multi-stage conversational flow (category, service, vendor, workflow generation)
- Retrieval-augmented generation (RAG) using ChromaDB and sentence-transformers
- Vendor and service recommendations based on real health metrics
- Extensible knowledge base for services and vendors
- Modular Python codebase

## Project Structure
```
├── knowledge_base/
│   ├── list_of_services.json
│   ├── services/           # Service metadata (e.g., pan_advanced.json)
│   └── vendors/            # Vendor health and info (e.g., vendor_health.json)
├── scripts/
│   ├── main.py             # Main chatbot entry point
│   ├── prompt_utils.py     # Prompt templates and rules
│   ├── query_db.py         # Vector DB retrieval logic
│   ├── state_manager.py    # Conversation/session state
│   ├── chunking.py, embedding.py, test_retrieval.py, etc.
├── vector_db/              # ChromaDB persistent storage
├── requirements.txt        # Python dependencies
└── README.md

- Ignore the files -> current_git_main.py and test_retrival.py
```

## Setup Instructions
1. **Clone the repository**
2. **Install Python 3.10+** (recommended: 3.13.5)
3. **Create and activate a virtual environment**
   ```sh
   python3 -m venv .prompt-engg
   source .prompt-engg/bin/activate
   ```
4. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
5. **Set up environment variables**
   - Copy `.env.example` to `.env` and fill in required keys (e.g., GROQ_API_KEY)

## Running the Chatbot
```sh
python3 scripts/main.py
```

## Usage
- Follow the chatbot prompts to select a category, service, and vendor.
- The chatbot will recommend vendors based on your priorities and real health metrics.
- At the end, a workflow JSON is generated for API integration.

## Extending the Knowledge Base
- Add new services to `knowledge_base/services/`
- Add or update vendor health data in `knowledge_base/vendors/`

## Dependencies
See `requirements.txt` for all Python dependencies.

## Notes
- Requires internet access for model downloads and API calls.
- For production, review and secure all environment variables and API keys.

## Author
- Aryan Balodi
