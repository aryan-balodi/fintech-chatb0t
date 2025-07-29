import json
import re

def sentence_chunking(text):
    # Splits text into individual sentences.
    return re.split(r'(?<=[.!?])\s+', text.strip()) if text else []

def chunk_vendor_health_json(vendor_health_json):
    """Special chunking for vendor health data to extract individual vendor metrics."""
    chunks = []
    
    def build_chunk(name, content, vendor_name=None):
        meta = {
            "type": "vendor_health",
            "file_path": "vendors/vendor_health.json"
        }
        if vendor_name:
            meta["vendor_name"] = vendor_name
        return {
            "chunk_name": name,
            "content": content,
            "metadata": meta
        }
    
    # 1. File overview
    description = vendor_health_json.get("description", "")
    if description:
        chunks.append(build_chunk("Vendor Health Overview", description))
    
    # 2. Individual vendor metrics (this is the key part!)
    data = vendor_health_json.get("data", {})
    row_data = data.get("rowData", [])
    
    for vendor_data in row_data:
        vendor_name = vendor_data.get("name", "")
        if vendor_name:
            # Create a comprehensive vendor metrics chunk
            metrics_parts = [f"Vendor: {vendor_name}"]
            
            # Add all available metrics
            for key, value in vendor_data.items():
                if key != "name" and value is not None:
                    metrics_parts.append(f"{key}: {value}")
            
            vendor_content = " | ".join(metrics_parts)
            chunks.append(build_chunk(f"Vendor Metrics: {vendor_name}", vendor_content, vendor_name))
    
    return chunks

def chunk_service_json(service_json):
    chunks = []

    category = service_json.get('category', '')
    service_name = service_json.get('service_name', '')

    def build_chunk(name, content, ctype=None):
        meta = {"category": category, 
                "service_name": service_name,
        }

        tags = service_json.get("tags", [])
        if tags:
            meta["tags"] = ', '.join(tags)

        vendors = service_json.get("available_vendors", [])
        if vendors:
            meta["available_vendors"] = ', '.join(vendors)
            
        if ctype:
            meta["type"] = ctype
        return {
            "chunk_name": name,
            "content": content,
            "metadata": meta
        }

    # 1. Service Overview (combine key fields for better context)
    overview_parts = []
    if category:
        overview_parts.append(f"Category: {category}")
    if service_name:
        overview_parts.append(f"Service: {service_name}")
    if service_json.get("description"):
        overview_parts.append(f"Description: {service_json['description']}")
    if service_json.get("llm_summary"):
        overview_parts.append(f"Summary: {service_json['llm_summary']}")
    
    if overview_parts:
        chunks.append(build_chunk("Service Overview", " | ".join(overview_parts), "overview"))

    # 2. Use Cases (grouped for better context)
    use_cases = service_json.get("use_cases", [])
    if use_cases:
        use_cases_text = "Use Cases: " + " | ".join([f"{i+1}. {uc}" for i, uc in enumerate(use_cases)])
        chunks.append(build_chunk("Use Cases", use_cases_text, "use_cases"))

    # 3. Tags and Vendors
    if service_json.get("tags"):
        tags_str = ', '.join(service_json["tags"])
        chunks.append(build_chunk("Tags", f"Tags: {tags_str}", "tags"))
    
    if service_json.get("available_vendors"):
        vendors_str = ', '.join(service_json["available_vendors"])
        chunks.append(build_chunk("Available Vendors", f"Available Vendors: {vendors_str}", "vendors"))

    # 4. Request Schema (grouped for better understanding)
    request_schema = service_json.get("request_schema", [])
    if request_schema:
        schema_parts = ["Request Schema:"]
        for field in request_schema:
            field_name = field.get('field', '')
            field_desc = field.get('description', '')
            field_type = field.get('type', '')
            required = "required" if field.get('required', False) else "optional"
            schema_parts.append(f"- {field_name} ({field_type}, {required}): {field_desc}")
        
        chunks.append(build_chunk("Request Schema", " | ".join(schema_parts), "request_schema"))

    # 5. Response Schema (grouped for better understanding)
    response_schema = service_json.get("response_schema", [])
    if response_schema:
        schema_parts = ["Response Schema:"]
        for field in response_schema:
            field_name = field.get('field', '')
            field_desc = field.get('description', '')
            field_type = field.get('type', '')
            required = "required" if field.get('required', False) else "optional"
            schema_parts.append(f"- {field_name} ({field_type}, {required}): {field_desc}")
        
        chunks.append(build_chunk("Response Schema", " | ".join(schema_parts), "response_schema"))

    # 6. Examples (if available)
    example_request = service_json.get("example_request")
    if example_request:
        chunks.append(build_chunk(
            "Example Request",
            f"Example Request: {json.dumps(example_request, indent=2)}",
            "example_request"
        ))

    example_response = service_json.get("example_response")
    if example_response:
        chunks.append(build_chunk(
            "Example Response",
            f"Example Response: {json.dumps(example_response, indent=2)}",
            "example_response"
        ))

    # 7. Integration details
    integration = service_json.get("integration")
    if integration:
        chunks.append(build_chunk(
            "Integration Details",
            f"Integration: {json.dumps(integration, indent=2)}",
            "integration"
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
