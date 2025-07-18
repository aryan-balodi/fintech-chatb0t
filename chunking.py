import json
import re

def sentence_chunking(text):
    # Splits text into individual sentences.
    return re.split(r'(?<=[.!?])\s+', text.strip()) if text else []

def chunk_service_json(service_json):
    chunks = []

    category = service_json.get('category', '')
    service_name = service_json.get('service_name', '')

    def build_chunk(name, content, ctype=None):
        meta = {"category": category, "service_name": service_name}
        if ctype:
            meta["type"] = ctype
        return {
            "chunk_name": name,
            "content": content,
            "metadata": meta
        }

    # 1. Category as a chunk
    chunks.append(build_chunk("Category", category))

    # 2. Service Name
    chunks.append(build_chunk("Service Name", service_name))

    # 3. Description sentences
    for i, sent in enumerate(sentence_chunking(service_json.get("description", ""))):
        chunks.append(build_chunk(f"Description Sentence {i+1}", sent))

    # 4. LLM Summary sentences
    for i, sent in enumerate(sentence_chunking(service_json.get("llm_summary", ""))):
        chunks.append(build_chunk(f"LLM Summary Sentence {i+1}", sent))

    # 5. Use Cases
    for i, uc in enumerate(service_json.get("use_cases", [])):
        chunks.append(build_chunk(f"Use Case {i+1}", uc))

    # 6. Tags
    if service_json.get("tags"):
        tags_str = ', '.join(service_json["tags"])
        chunks.append(build_chunk("Tags", f"Tags: {tags_str}"))

    # 7. Request Schema Fields
    for field in service_json.get("request_schema", []):
        chunks.append(build_chunk(
            f"Request Schema Field: {field.get('field', '')}",
            json.dumps(field, indent=2),
            ctype="request_schema"
        ))

    # 8. Response Schema Fields
    for field in service_json.get("response_schema", []):
        chunks.append(build_chunk(
            f"Response Schema Field: {field.get('field', '')}",
            json.dumps(field, indent=2),
            ctype="response_schema"
        ))

    # 9. Example Request
    example_request = service_json.get("example_request")
    if example_request:
        chunks.append(build_chunk(
            "Example Request",
            json.dumps(example_request, indent=2),
            ctype="example_request"
        ))

    # 10. Example Response
    example_response = service_json.get("example_response")
    if example_response:
        chunks.append(build_chunk(
            "Example Response",
            json.dumps(example_response, indent=2),
            ctype="example_response"
        ))

    # 11. Integration
    integration = service_json.get("integration")
    if integration:
        chunks.append(build_chunk(
            "Integration Details",
            json.dumps(integration, indent=2),
            ctype="integration"
        ))

    return chunks

# Usage example:
if __name__ == "__main__":
    with open('pan_advanced.json') as f:
        service_json = json.load(f)
    chunks = chunk_service_json(service_json)
    # Print or process your chunks as needed
    for chunk in chunks:
        print(f"--- {chunk['chunk_name']} ---")
        print(chunk["content"])
        print("Metadata:", chunk["metadata"])
        print("-" * 40)
    print(f"Total chunks returned: {len(chunks)}")
