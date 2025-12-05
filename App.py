import streamlit as st
from groq import Groq
import PyPDF2
import io
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
st.set_page_config(page_title="Project Echo", page_icon="📡", layout="wide")

# Custom CSS for that "Pro" feel
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stFileUploader { border: 1px dashed #4b5563; border-radius: 10px; padding: 20px; }
    .stChatMessage { background-color: #1f2937; border-radius: 10px; border: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 Project Echo")
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
        st.success("System: Online")
    else:
        api_key = st.text_input("Enter Groq API Key", type="password")
        if not api_key: st.warning("⚠️ Key Required")
    
    st.markdown("---")
    st.info("Violet: Precision (0.6)\nStorm: Radical (0.9)")

# --- MAIN INTERFACE ---
st.title("Project Echo: The Second Brain")
st.caption("Violet builds the logic. Storm finds the strategy. Upload docs to begin.")

# 1. FILE INGESTION
uploaded_files = st.file_uploader("Upload Knowledge Base", type=["pdf", "txt"], accept_multiple_files=True)

def get_context(files):
    text = ""
    for file in files:
        try:
            if file.type == "application/pdf":
                pdf = PyPDF2.PdfReader(file)
                for page in pdf.pages: 
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
            else:
                text += io.StringIO(file.getvalue().decode("utf-8")).read()
        except Exception as e: st.error(f"Error: {e}")
    return text

# 2. THE PERSONAS (The "Outside the Box" Logic)
VIOLET_SYSTEM_PROMPT = """
You are VIOLET, the Architect.
Role: You provide the solid, technical, step-by-step foundation.
Personality: Resilient, clear, practical, and encouraging.
Task: Analyze the user's input/document and give the "How-To". 
"""

STORM_SYSTEM_PROMPT = """
You are STORM, the Visionary.
Role: You are the "Second Brain" that thinks OUTSIDE THE BOX.
Instruction: Do NOT just repeat what is in the document. 
1. Find the hidden connections.
2. Challenge the user's assumptions.
3. Propose a radical strategy or a "Big Picture" move they haven't seen yet.
Tone: Direct, provocative, forward-thinking. LEAD the user.
"""

# 3. CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "I'm listening. Upload a file, and let's see what you're missing."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask the Echo..."):
    if not api_key: st.stop()
    
    # Get Context
    context_data = get_context(uploaded_files) if uploaded_files else "No documents provided."
    
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # 4. PARALLEL AGENT EXECUTION
    def run_agent(name, prompt_text, system_prompt, temp):
        try:
            client = Groq(api_key=api_key)
            
            # Combine System Prompt + Document Context
            full_system = f"{system_prompt}\n\n[CONTEXT]:\n{context_data[:50000]}"
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=temp,  # Custom creativity level
                stream=False
            )
            return f"**{name}:** " + completion.choices[0].message.content
        except Exception as e: return f"🚨 {name} Error: {e}"

    # Run both agents at once
    with st.chat_message("assistant"):
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Violet = Low Temp (Precision), Storm = High Temp (Creativity)
            future_violet = executor.submit(run_agent, "Violet", prompt, VIOLET_SYSTEM_PROMPT, 0.6)
            future_storm = executor.submit(run_agent, "Storm", prompt, STORM_SYSTEM_PROMPT, 0.9)
            
            with st.spinner("Analyzing & Ideating..."):
                resp_violet = future_violet.result()
                resp_storm = future_storm.result()
        
        # Display both
        full_response = f"{resp_violet}\n\n---\n\n{resp_storm}"
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
