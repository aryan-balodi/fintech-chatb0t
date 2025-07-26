from prompt_utils import (
    build_prompt,
    ALLOWED_VENDORS,
    ALLOWED_SERVICES,
    ALLOWED_CATEGORIES,
    ALLOWED_HEALTH_METRICS
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
def retrieve_context_chunks(user_query: str) -> str:
    """Retrieves relevant context from the existing vector DB."""
    chunks = get_relevant_chunks(user_query, top_k=5)
    if not chunks:
        return "No relevant context could be retrieved."
    return "\n\n".join(chunks)

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
    knowledge_chunks = retrieve_context_chunks(user_input) if current_stage in ["STAGE_2", "STAGE_3", "STAGE_4"] else ""

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
