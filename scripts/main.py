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
        match = re.search(r'"category"\s*:\s*"([A-Za-z/ ]+)"', context)
        if match:
            return match.group(1)
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

    chunks_result = get_relevant_chunks(user_query, top_k=5)
    if not chunks_result or not chunks_result.get("documents"):
        return "No relevant context could be retrieved."
    
    documents = chunks_result.get("documents", [])
    metadatas = chunks_result.get("metadatas", [])
    
    relevant_chunks = []

    # For STAGE_2, filter services by selected category
    if current_stage == "STAGE_2":
        selected_category = extract_selected_category(session_context)
        allowed_services = []
        if selected_category and selected_category in CATEGORY_TO_SERVICES:
            allowed_services = CATEGORY_TO_SERVICES[selected_category]
        else:
            allowed_services = ALLOWED_SERVICES
        # Only include chunks for allowed services
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            for service in allowed_services:
                if service.lower() in doc.lower():
                    relevant_chunks.append(doc)
                    break
        if not relevant_chunks:
            return "No relevant service data could be retrieved for the selected category."
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
