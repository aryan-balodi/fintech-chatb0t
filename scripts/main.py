from prompt_utils import build_prompt
from state_manager import SessionManager
from query_db import get_relevant_chunks
from groq import Groq
from dotenv import load_dotenv
import os

# === Config ===
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.1-8b-instant"  # Use a Groq-supported model

# === Groq Client Setup ===
client = Groq(api_key=GROQ_API_KEY)

# === Call Groq Cloud LLM ===
def call_llm(prompt: str) -> str:
    """
    Sends the prompt to Groq and returns the assistant's reply.
    """
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
    """
    Retrieves relevant context from the existing vector DB.
    """
    chunks = get_relevant_chunks(user_query, top_k=5)
    if not chunks:
        return "No relevant context could be retrieved."
    return "\n\n".join(chunks)

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

    # STEP 1: Get context and stage
    current_stage = sm.get_stage(session_id)
    session_context = sm.get_context(session_id)

    # STEP 2: Retrieve context via RAG (for later stages)
    knowledge_chunks = retrieve_context_chunks(user_input) if current_stage in ["STAGE_2", "STAGE_3", "STAGE_4"] else ""

    # STEP 3: Build the LLM prompt
    prompt = build_prompt(
        user_query=user_input,
        stage=current_stage,
        session_context=session_context,
        knowledge_chunks=knowledge_chunks
    )

    # STEP 4: Invoke the Groq LLM API
    print("\n🤖 Thinking...\n")
    assistant_reply = call_llm(prompt)

    # STEP 5: Update session memory with this turn
    sm.update(session_id, user_input, assistant_reply)

    # STEP 6: Display assistant response
    print(f"\n🤖 Assistant ({current_stage}):\n{assistant_reply}\n")
