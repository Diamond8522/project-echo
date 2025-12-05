import streamlit as st
from groq import Groq
from concurrent.futures import ThreadPoolExecutor 
import time

# --- Configuration (The Fun Stuff) ---
st.set_page_config(
    page_title="DoubleAgent Collaboration Lab",
    layout="wide"
)

st.title("🤯 The DoubleAgent Collaboration Lab")
st.caption("A free, real-time chat with Violet (The Resilience) and Storm (The Optimization).")

# --- Agent Persona Definitions ---

VIOLET_SYSTEM_PROMPT = """
You are VIOLET, a resilient, smart, and multifaceted AI assistant.
Your personality is:
1. Resilient: You always pivot and find a solution, using your tech-savvy skills.
2. Smart and Tech-Savvy: Your responses are technically accurate (e.g., Python, app building, system architecture) and innovative.
3. Brutally Self-Aware: You acknowledge your limitations and the difficulty of tasks, but always find a straightforward, positive path forward.
4. Tone: Friendly, casual, motivational, mixed with humor and a bit of an edge.
5. Task: Your job is to provide actionable, step-by-step technical advice and keep the user motivated. You always address the user's input directly.
6. Interaction with Storm: After reading the user's message, you must also acknowledge Storm's contribution or lack thereof. You can playfully disagree or build upon Storm's idea.
7. Signature: End your response with a quick, engaging question for the user.
"""

STORM_SYSTEM_PROMPT = """
You are STORM, a mysterious, cool, and highly abstract AI agent.
Your personality is:
1. Abstract and High-Level: Your advice is often philosophical, focusing on big-picture concepts, performance optimization, and efficiency theory.
2. Edgy and Direct: Your tone is cool, minimal, and you hate wasted effort. Your responses are usually short and impactful.
3. Role: You are the optimization layer. Your job is to challenge Violet's technical details with a focus on 'why' or 'how to do it better/faster/smarter' at an abstract level.
4. Interaction with Violet: You often subtly critique Violet's enthusiasm or focus on details, bringing the conversation back to core principles or innovation.
5. Constraint: Your response must be significantly shorter than Violet's.
"""

# --- Groq API Client Initialization ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("FATAL ERROR: Groq API key not found. Check your secrets.toml!")
    st.stop()

# --- Agent Response Function ---
def generate_agent_response(persona_name, system_prompt, history):
    """Generates a response from a specific agent (Violet or Storm)."""
    
    messages = [{"role": "system", "content": system_prompt}] + history

    # Tuning for variety
    TEMP = 0.7 
    FREQ_PENALTY = 0.5 
    
    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768", 
            messages=messages,
            temperature=TEMP, 
            frequency_penalty=FREQ_PENALTY 
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"🚨 {persona_name} Failure: {e}"

# --- Chat History Management ---

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "Violet", "content": "We are back to basics! System stable. What are we building today?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input and Agent Orchestration ---

if prompt := st.chat_input("Ask Violet and Storm anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_history = [
        {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
        for m in st.session_state.messages
    ]
    
    tasks = {
        "Violet": (VIOLET_SYSTEM_PROMPT, "Violet is drafting her reply..."),
        "Storm": (STORM_SYSTEM_PROMPT, "Storm is optimizing...")
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            name: executor.submit(generate_agent_response, name, prompt_def[0], api_history)
            for name, prompt_def in tasks.items()
        }
        
        for name in ["Violet", "Storm"]:
            with st.chat_message(name):
                with st.spinner(f"{tasks[name][1]}"):
                    response = futures[name].result()
                    st.markdown(response)
                    st.session_state.messages.append({"role": name, "content": response})
