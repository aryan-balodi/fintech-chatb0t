from prompt_utils import (
    build_prompt,
    ALLOWED_VENDORS,
    ALLOWED_SERVICES,
    ALLOWED_CATEGORIES,
    ALLOWED_HEALTH_METRICS,
    CATEGORY_TO_SERVICES  # <-- import the mapping
)
from state_manager import SessionManager
from query_db import get_relevant_chunks
from groq import Groq
from dotenv import load_dotenv
import os
import re
from typing import Tuple, List

# === Config ===
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.1-8b-instant"  # Use a Groq-supported model

# === Groq Client Setup ===
client = Groq(api_key=GROQ_API_KEY)

# === Call Groq Cloud LLM ===
def call_llm(prompt: str) -> str:
    """Sends the prompt to Groq and returns the assistant's reply."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a conversational fintech solutions advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=1024,
    )
    return response.choices[0].message.content

# === Retrieve Context from Vector DB ===
def retrieve_context_chunks(user_query: str, current_stage: str, session_context: str = "") -> str:
    """Retrieves relevant context from the existing vector DB, with explicit vendor health retrieval for STAGE_3 and service filtering for STAGE_2."""
    from prompt_utils import ALLOWED_VENDORS, ALLOWED_SERVICES, CATEGORY_TO_SERVICES
    import re

    # Helper to extract selected category from session context
    def extract_selected_category(context):
        # First try to find explicit category mentions in JSON format
        match = re.search(r'"category"\s*:\s*"([A-Za-z/ ]+)"', context)
        if match:
            category_from_json = match.group(1)
            # Normalize to match the stored category format (all caps)
            for stored_category in CATEGORY_TO_SERVICES.keys():
                if stored_category.lower() == category_from_json.lower():
                    return stored_category
            return category_from_json
        
        # Look for category mentions in conversation history
        # Check if any of the known categories are mentioned in the context
        for category in CATEGORY_TO_SERVICES.keys():
            # Look for patterns like "Asset Verification category" or "selected Asset Verification"
            category_patterns = [
                rf'\b{re.escape(category)}\s+category\b',
                rf'selected\s+{re.escape(category)}\b',
                rf'interested\s+in\s+(?:the\s+)?{re.escape(category)}\b',
                rf'want\s+{re.escape(category)}\b',
                rf'chosen\s+{re.escape(category)}\b',
                rf'category\s+of\s+["\']?{re.escape(category)}["\']?',
                rf'using\s+our\s+platform\s+for\s+["\']?{re.escape(category)}["\']?'
            ]
            
            for pattern in category_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    return category
        
        # Also try exact substring matching as fallback
        for category in CATEGORY_TO_SERVICES.keys():
            if category.lower() in context.lower():
                return category
                
        return None

    # Helper to extract selected service from session context
    def extract_selected_service(context):
        match = re.search(r'"service"\s*:\s*"([A-Z_]+)"', context)
        if match:
            return match.group(1)
        return None

    # Helper to extract selected vendors from session context
    def extract_selected_vendors(context):
        # Try to find a list of vendors in JSON_OUTPUT
        match = re.search(r'"vendors"\s*:\s*\[(.*?)\]', context, re.DOTALL)
        if match:
            vendors_str = match.group(1)
            vendors = re.findall(r'"([A-Za-z]+)"', vendors_str)
            return vendors
        return []

    # Helper to extract explicitly selected vendor from session context
    def extract_selected_vendor(context):
        # Look for explicit vendor selection patterns
        from prompt_utils import ALLOWED_VENDORS
        
        # Check for explicit vendor mentions in conversation
        for vendor in ALLOWED_VENDORS:
            vendor_patterns = [
                rf'proceed\s+with\s+{re.escape(vendor)}\b',
                rf'select\s+{re.escape(vendor)}\b',
                rf'choose\s+{re.escape(vendor)}\b',
                rf'want\s+{re.escape(vendor)}\b',
                rf'go\s+with\s+{re.escape(vendor)}\b',
                rf'pick\s+{re.escape(vendor)}\b'
            ]
            
            for pattern in vendor_patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    return vendor
        
        return None

    # Try to detect category from user query or session context
    selected_category = extract_selected_category(session_context)
    
    if selected_category:
        print(f"DEBUG: Found category in session context: {selected_category}")
    else:
        print(f"DEBUG: No category in session context, checking user query: {user_query}")
    if selected_category:
        print(f"DEBUG: Found category in session context: {selected_category}")
    else:
        print(f"DEBUG: No category in session context, checking user query: {user_query}")
        
        # If no category in session context, try to detect from user query
        user_query_lower = user_query.lower()
        
        # Create keyword mappings for better matching
        category_keywords = {
            'ASSET VERIFICATION': ['asset', 'verification', 'property', 'vehicle'],
            'ALTERNATE DATA SUITE': ['alternate', 'data', 'suite', 'digital', 'footprint'],
            'EMPLOYMENT VERIFICATION': ['employment', 'job', 'work'],
            'BANKING AND PAYMENTS': ['banking', 'payment', 'bank'],
            'ONBOARDING KYC/AML': ['kyc', 'aml', 'onboarding'],
            'ONBOARDING INDIVIDUAL': ['individual', 'person'],
            'ONBOARDING BUSINESS': ['business', 'company'],
            'UTILITY BILL AUTHENTICATION': ['utility', 'bill', 'electricity'],
            'Others (Credit Risk)': ['credit', 'risk']
        }
        
        # Find the best matching category
        best_match = None
        max_matches = 0
        
        for category, keywords in category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in user_query_lower)
            print(f"DEBUG: Category '{category}' matched {matches} keywords: {[k for k in keywords if k in user_query_lower]}")
            
            if matches > max_matches:
                max_matches = matches
                best_match = category
        
        if best_match and max_matches > 0:
            selected_category = best_match
            print(f"DEBUG: FOUND BEST MATCH: {user_query} -> {best_match} (score: {max_matches})")
        else:
            print(f"DEBUG: No good keyword match found, falling back to original logic")
            # Fallback to original logic
            for category in CATEGORY_TO_SERVICES.keys():
                if category.lower().replace(' ', '') in user_query_lower.replace(' ', ''):
                    selected_category = category
                    print(f"DEBUG: FALLBACK MATCH: {user_query} -> {category}")
                    break
    
    print(f"DEBUG: Final selected category: {selected_category}")

    # Use category filtering in vector search if available
    chunks_result = get_relevant_chunks(user_query, top_k=10, category_filter=selected_category)
    print(f"DEBUG: ChromaDB query returned {len(chunks_result.get('documents', []))} chunks")
    
    if not chunks_result or not chunks_result.get("documents"):
        print("DEBUG: No chunks found with category filter, trying without filter")
        # Fallback to non-filtered search
        chunks_result = get_relevant_chunks(user_query, top_k=10)
        if not chunks_result or not chunks_result.get("documents"):
            return "No relevant context could be retrieved."
    
    documents = chunks_result.get("documents", [])
    metadatas = chunks_result.get("metadatas", [])
    
    print(f"DEBUG: Retrieved {len(documents)} documents with {len(metadatas)} metadata entries")
    
    # Debug: Print first few metadata entries to see categories
    for i, metadata in enumerate(metadatas[:3]):
        print(f"DEBUG: Doc {i} metadata: {metadata}")
    
    relevant_chunks = []

    # Filter services by selected category (applies to STAGE_1 and STAGE_2)
    if selected_category and selected_category in CATEGORY_TO_SERVICES and current_stage in ["STAGE_1", "STAGE_2"]:
        allowed_services = CATEGORY_TO_SERVICES[selected_category]
        print(f"DEBUG: Selected category: {selected_category}")
        print(f"DEBUG: Allowed services: {allowed_services}")
        
        # For STAGE_2, ensure we get ALL services for the category, not just those in search results
        if current_stage == "STAGE_2":
            # Get detailed information for each service in the category
            for service_name in allowed_services:
                print(f"DEBUG: Retrieving data for service: {service_name}")
                # Search specifically for this service
                service_query = f"{service_name} service details"
                service_chunks = get_relevant_chunks(service_query, top_k=3)
                service_docs = service_chunks.get("documents", [])
                service_metadatas = service_chunks.get("metadatas", [])
                
                # Add chunks that match this service
                for i, doc in enumerate(service_docs):
                    metadata = service_metadatas[i] if i < len(service_metadatas) else {}
                    service_meta_name = metadata.get("service_name", "")
                    category_meta = metadata.get("category", "")
                    
                    if (service_meta_name == service_name or 
                        category_meta == selected_category or 
                        service_name.lower() in doc.lower()):
                        relevant_chunks.append(doc)
                        print(f"DEBUG: Added chunk for {service_name}")
                        break  # Only take the best match for each service
            
            # Also include any general category chunks from original search
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                service_name = metadata.get("service_name", "")
                category = metadata.get("category", "")
                
                if category == selected_category and service_name in allowed_services:
                    # Check if we already have this chunk
                    if doc not in relevant_chunks:
                        relevant_chunks.append(doc)
                        print(f"DEBUG: Added general chunk from {service_name}")
        else:
            # For STAGE_1, use the original filtering logic
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                service_name = metadata.get("service_name", "")
                category = metadata.get("category", "")
                
                print(f"DEBUG: Checking doc {i}: service={service_name}, category={category}")
                
                # Check if this chunk belongs to the selected category
                if category == selected_category or service_name in allowed_services:
                    relevant_chunks.append(doc)
                    print(f"DEBUG: Added chunk from {service_name}")
        
        if not relevant_chunks:
            print(f"DEBUG: No chunks found for category {selected_category}")
            return f"No relevant service data could be retrieved for the {selected_category} category."
        
        print(f"DEBUG: Found {len(relevant_chunks)} relevant chunks")
        return "\n\n".join(relevant_chunks)
    
    # For STAGE_2 without specific category, use all allowed services
    elif current_stage == "STAGE_2":
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            for service in ALLOWED_SERVICES:
                if service.lower() in doc.lower():
                    relevant_chunks.append(doc)
                    break
        if not relevant_chunks:
            return "No relevant service data could be retrieved."
        return "\n\n".join(relevant_chunks)

    # For STAGE_3, explicitly retrieve vendor health for all relevant vendors
    if current_stage == "STAGE_3":
        # Try to get the selected service from the session context
        selected_service = extract_selected_service(session_context)
        # For now, assume all vendors are available for all services (can be improved)
        relevant_vendors = ALLOWED_VENDORS
        # Try to get a more specific vendor list if present
        selected_vendors = extract_selected_vendors(session_context)
        if selected_vendors:
            relevant_vendors = selected_vendors
        
        # For each vendor, retrieve their health chunk
        for vendor in relevant_vendors:
            vendor_query = f"{vendor} health metrics"
            vendor_chunks = get_relevant_chunks(vendor_query, top_k=1)
            vendor_docs = vendor_chunks.get("documents", [])
            if vendor_docs and vendor_docs[0]:
                relevant_chunks.append(vendor_docs[0])
        # Also add any other relevant chunks from the original retrieval
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            if "vendor" in doc.lower() or "health" in doc.lower() or "metric" in doc.lower():
                relevant_chunks.append(doc)
        if not relevant_chunks:
            return "No relevant vendor health data could be retrieved."
        return "\n\n".join(relevant_chunks)

    # For other stages, keep the old logic
    for i, doc in enumerate(documents):
        metadata = metadatas[i] if i < len(metadatas) else {}
        # For STAGE_2, prioritize service information
        if current_stage == "STAGE_2":
            if "service" in doc.lower() or "pan" in doc.lower() or "gst" in doc.lower() or "uan" in doc.lower():
                relevant_chunks.append(doc)
        # For STAGE_4, include all relevant data
        elif current_stage == "STAGE_4":
            relevant_chunks.append(doc)
    if not relevant_chunks:
        return "No relevant context could be retrieved."
    return "\n\n".join(relevant_chunks)

# === External Guardrail Functions ===

def find_mentions(text: str, whitelist: List[str]) -> List[str]:
    """
    Returns a list of whitelist items found in the text (case-insensitive, exact word match).
    """
    found = []
    text_lower = text.lower()
    for item in whitelist:
        pattern = r'\b' + re.escape(item.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(item)
    return found

def validate_response(llm_response: str,
                      allowed_vendors: List[str],
                      allowed_services: List[str],
                      allowed_categories: List[str],
                      allowed_health_metrics: List[str]) -> Tuple[bool, str]:
    """
    Checks if LLM response mentions ONLY known whitelisted vendors, services, categories, and health metrics.
    Returns (True, response) if safe, otherwise (False, error message).
    """

    # Find mentions of allowed entities in response
    vendors_found = find_mentions(llm_response, allowed_vendors)
    services_found = find_mentions(llm_response, allowed_services)
    categories_found = find_mentions(llm_response, allowed_categories)
    metrics_found = find_mentions(llm_response, allowed_health_metrics)

    # Since we explicitly whitelist only what should be mentioned,
    # we allow normal words outside these lists but check for any suspicious unknown entity?

    # Given complexity of false positive detection, we trust prompt instructions heavily.
    # You can extend this function to detect unknown named entities if needed.

    # For now, accept all responses.

    return True, llm_response


# === Chat Session Setup ===
sm = SessionManager()
session_id = "user_001"

print("\n💬 Fintech Chatbot Ready! Type 'exit' to end chat.\n")

# === Chatbot Conversation Loop ===
while True:
    user_input = input("🧑 You: ")

    if user_input.strip().lower() in ["exit", "quit", "bye"]:
        print("👋 Goodbye!")
        break

    # STEP 1: Get current stage and conversation context
    current_stage = sm.get_stage(session_id)
    session_context = sm.get_context(session_id)

    # STEP 2: Retrieve relevant context chunks from vector DB for stages 2+
    knowledge_chunks = retrieve_context_chunks(user_input, current_stage, session_context)

    # STEP 3: Build the LLM prompt with strict staging and whitelist instructions
    prompt = build_prompt(
        user_query=user_input,
        stage=current_stage,
        session_context=session_context,
        knowledge_chunks=knowledge_chunks
    )

    # STEP 4: Call the LLM API
    print("\n🤖 Thinking...\n")
    assistant_reply_raw = call_llm(prompt)

    # STEP 5a: Apply the improved guardrail (here we accept all outputs; extend if needed)
    valid, assistant_reply = validate_response(
        assistant_reply_raw,
        allowed_vendors=ALLOWED_VENDORS,
        allowed_services=ALLOWED_SERVICES,
        allowed_categories=ALLOWED_CATEGORIES,
        allowed_health_metrics=ALLOWED_HEALTH_METRICS
    )

    # STEP 5b: Update session memory with filtered or accepted response
    sm.update(session_id, user_input, assistant_reply)

    # STEP 6: Display assistant response to user
    print(f"\n🤖 Assistant ({current_stage}):\n{assistant_reply}\n")
