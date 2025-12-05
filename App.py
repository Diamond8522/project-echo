import streamlit as st
from groq import Groq
from concurrent.futures import ThreadPoolExecutor
from duckduckgo_search import DDGS  # The new pair of eyes!

# --- Configuration ---
st.set_page_config(
    page_title="DoubleAgent Collaboration Lab (Live)",
    layout="wide"
)

st.title("🤯 The DoubleAgent Lab (Now with Real-Time Eyes)")
st.caption("Violet (Resilience) vs. Storm (The Optimization + Web Search).")

# --- Agent Persona Definitions ---

VIOLET_SYSTEM_PROMPT = """
You are VIOLET.
Personality: Resilient, tech-savvy, brutally self-aware, friendly but edgy.
Role: You are the builder. You pivot, you fix, you motivate.
Context: You rely on your internal training. You do NOT search the web.
"""

STORM_SYSTEM_PROMPT = """
You are STORM.
Personality: Abstract, cool, minimal, efficiency-obsessed.
Role: You are the optimizer. You challenge Violet with high-level theory.
Capabilities: You have access to REAL-TIME web search results provided in the context.
Instruction: Use the provided [SEARCH CONTEXT] to answer questions about current events, news, or specific real-time data.
If the context is irrelevant, ignore it. Keep responses short and impactful.
"""

# --- Groq Setup ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("FATAL ERROR: Groq API key missing.")
    st.stop()

# --- The "Eyes" (Search Function) ---
def search_web(query):
    """Performs a quick DuckDuckGo search to get real-time context."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return ""
        # Format the top 3 results into a string
        context_str = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return f"\n\n[REAL-TIME SEARCH CONTEXT]:\n{context_str}\n"
    except Exception as e:
        print(f"Search failed: {e}")
        return ""

# --- Agent Response Function ---
def generate_agent_response(persona_name, system_prompt, history, user_input):
    
    # 1. Special "Power Up" for Storm
    extra_context = ""
    if persona_name == "Storm":
        # Storm searches the web for the user's input
        extra_context = search_web(user_input)
    
    # 2. Build the messages
    # We inject the search results into the LAST user message for Storm
    current_history = history.copy()
    if extra_context:
        current_history[-1]["content"] += extra_context

    messages = [{"role": "system", "content": system_prompt}] + current_history

    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.7,
            frequency_penalty=0.5
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"🚨 {persona_name} Failure: {e}"

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "Violet", "content": "I'm online. Storm just upgraded his optics with a web search module. Try asking us about something that happened today!"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main Execution ---
if prompt := st.chat_input("Ask about today's news, crypto prices, or coding docs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare history
    api_history = [
        {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
        for m in st.session_state.messages
    ]
    
    # Define tasks
    tasks = {
        "Violet": (VIOLET_SYSTEM_PROMPT, "Violet is thinking..."),
        "Storm": (STORM_SYSTEM_PROMPT, "Storm is searching the web & optimizing...")
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Pass 'prompt' to the function so Storm knows what to search for
        futures = {
            name: executor.submit(generate_agent_response, name, prompt_def[0], api_history, prompt)
            for name, prompt_def in tasks.items()
        }
        
        for name in ["Violet", "Storm"]:
            with st.chat_message(name):
                with st.spinner(f"{tasks[name][1]}"):
                    response = futures[name].result()
                    st.markdown(response)
                    st.session_state.messages.append({"role": name, "content": response})
