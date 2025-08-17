import os
import json

def load_json_files(root_folder):
    """Load all JSON files into memory."""
    knowledge_base = []
    for dirpath, _, filenames in os.walk(root_folder):
        for fname in filenames:
            if fname.lower().endswith('.json'):
                file_path = os.path.join(dirpath, fname)
                with open(file_path, 'r', encoding='utf-8') as f:
                    knowledge_base.append(json.load(f))
    return knowledge_base

def load_json_files_by_type(root_folder):
    """Load JSON files into separate categories."""
    services = []
    vendors = []
    list_of_services = None

    for dirpath, _, filenames in os.walk(root_folder):
        for fname in filenames:
            if fname.lower().endswith('.json'):
                file_path = os.path.join(dirpath, fname)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "services" in dirpath:
                        services.append(data)
                    elif "vendors" in dirpath:
                        vendors.append(data)
                    elif fname == "list_of_services.json":
                        list_of_services = data
    return services, vendors, list_of_services

def organize_by_category(knowledge_base):
    """Organize services by category."""
    categorized_data = {}
    for service in knowledge_base:
        category = service.get('category', 'Uncategorized')
        if category not in categorized_data:
            categorized_data[category] = []
        categorized_data[category].append(service)
    return categorized_data

def organize_services_by_category(services):
    """Organize services by category."""
    categorized_data = {}
    for service in services:
        category = service.get('category', 'Uncategorized').lower()  # Normalize category to lowercase
        if category not in categorized_data:
            categorized_data[category] = []
        categorized_data[category].append(service)
    return categorized_data

def get_services_by_category(category, knowledge_base):
    """Retrieve services under a specific category."""
    results = []
    for service in knowledge_base:
        if service.get('category', '').lower() == category.lower():
            results.append(service)
    return results

def search_by_tags_or_description(query, knowledge_base):
    """Search services by tags or description."""
    results = []
    for service in knowledge_base:
        if query.lower() in service.get('description', '').lower() or \
           any(query.lower() in tag.lower() for tag in service.get('tags', [])):
            results.append(service)
    return results

def format_results_for_llm(results):
    """Format search results into a structured prompt."""
    formatted = []
    for result in results:
        formatted.append(f"Service: {result.get('service_name')}\n"
                         f"Category: {result.get('category')}\n"
                         f"Description: {result.get('description')}\n"
                         f"Tags: {', '.join(result.get('tags', []))}\n")
    return "\n".join(formatted)

if __name__ == "__main__":
    # Path to the knowledge base directory
    root_folder = "./knowledge_base"

    # Load the knowledge base
    print("Loading knowledge base...")
    services, vendors, list_of_services = load_json_files_by_type(root_folder)
    print(f"Loaded {len(services)} services.")
    print(f"Loaded {len(vendors)} vendor files.")
    print(f"Loaded list of services: {list_of_services is not None}")

    # Test: Get services by category
    category = "employment verification"  # Use lowercase for comparison
    print(f"\nServices under category '{category}':")
    services_by_category = organize_services_by_category(services).get(category, [])
    print(format_results_for_llm(services_by_category))

    # Test: Search services by tags or description
    query = "uan lookup"
    print(f"\nServices matching query '{query}':")
    search_results = search_by_tags_or_description(query, services)
    print(format_results_for_llm(search_results))
