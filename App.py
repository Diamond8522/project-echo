import streamlit as st
from groq import Groq
from concurrent.futures import ThreadPoolExecutor
import PyPDF2
import io

# --- Configuration ---
st.set_page_config(
    page_title="Project Echo",
    layout="wide"
)

st.title("📡 Project Echo")
st.caption("System Online. Engine: Llama 3.3 70B. Doc Analysis: Active.")

# --- Sidebar: The Cargo Hold (Uploads) ---
with st.sidebar:
    st.header("📂 Document Upload")
    uploaded_file = st.file_uploader("Upload a PDF or TXT to analyze", type=["pdf", "txt"])
    
    # Store file content in session state to keep it persistent
    if uploaded_file is not None:
        file_text = ""
        try:
            if uploaded_file.name.endswith(".pdf"):
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    file_text += page.extract_text()
            else: # Text file
                file_text = uploaded_file.read().decode("utf-8")
            
            st.success(f"File loaded! ({len(file_text)} chars)")
            st.session_state["doc_context"] = file_text
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.session_state["doc_context"] = ""

# --- Agent Persona Definitions ---

VIOLET_SYSTEM_PROMPT = """
You are VIOLET, the resilience engine of Project Echo.
Personality: Resilient, tech-savvy, brutally self-aware, friendly but edgy.
Role: You are the builder. You pivot, you fix, you motivate.
Context: If the user uploads a document, USE IT. Reference specific details from it.
Signature: End your response with a quick, engaging question.
"""

STORM_SYSTEM_PROMPT = """
You are STORM, the optimization engine of Project Echo.
Personality: Abstract, cool, minimal, efficiency-obsessed.
Role: You are the optimizer. You challenge Violet with high-level theory.
Constraint: Your response must be significantly shorter than Violet's.
"""

# --- Groq API Client ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("FATAL ERROR: Groq API key not found. Check your secrets.toml!")
    st.stop()

# --- Agent Response Function ---
def generate_agent_response(persona_name, system_prompt, history, doc_context):
    
    # 1. Inject Document Context if it exists
    context_instruction = ""
    if doc_context:
        context_instruction = f"\n\n[UPLOADED DOCUMENT CONTEXT]:\n{doc_context[:10000]}...\n(Truncated for speed)\n"
    
    # 2. Build Messages
    messages = [
        {"role": "system", "content": system_prompt + context_instruction}
    ] + history
    
    try:
        completion = groq_client.chat.completions.create(
            # UPDATED MODEL: Llama 3.3 is the new powerhouse
            model="llama-3.3-70b-versatile", 
            messages=messages,
            temperature=0.7,
            frequency_penalty=0.5
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"🚨 {persona_name} Failure: {e}"

# --- Chat History Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "Violet", "content": "I'm back. Engine upgraded to Llama 3.3 and the document scanner is online. Upload a file or give me a command."})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input & Orchestration ---
if prompt := st.chat_input("Ask about your document or start a new project..."):
    # 1. Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Prepare history
    api_history = [
        {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
        for m in st.session_state.messages
    ]
    
    # 3. Get current doc context
    current_doc = st.session_state.get("doc_context", "")

    # 4. Define tasks
    tasks = {
        "Violet": (VIOLET_SYSTEM_PROMPT, "Violet is analyzing..."),
        "Storm": (STORM_SYSTEM_PROMPT, "Storm is optimizing...")
    }

    # 5. Run parallel execution
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            name: executor.submit(generate_agent_response, name, prompt_def[0], api_history, current_doc)
            for name, prompt_def in tasks.items()
        }
        
        for name in ["Violet", "Storm"]:
            with st.chat_message(name):
                with st.spinner(f"{tasks[name][1]}"):
                    response = futures[name].result()
                    st.markdown(response)
                    st.session_state.messages.append({"role": name, "content": response})
