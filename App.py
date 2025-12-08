import streamlit as st
from groq import Groq
import PyPDF2
import io
from concurrent.futures import ThreadPoolExecutor

# --- 1. THE BRAINS (Functions must be at the top!) ---

def generate_blueprint(history, api_key):
    """Compiles the chat into a strategy document."""
    conversation = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
    
    prompt = f"""
    Analyze this conversation history between the User, Violet (Builder), Storm (Visionary), and Lex (Auditor).
    Create a structured "Project Blueprint" based on it.
    
    Format it exactly like this:
    # 🚀 PROJECT ECHO: STRATEGY REPORT
    
    ## 🧠 STORM'S VISION (The Big Picture)
    [Summarize the radical ideas and strategy here]
    
    ## 🛠 VIOLET'S BLUEPRINT (The Execution)
    [Bullet points of specific action steps]
    
    ## ⚖️ LEX'S AUDIT (Case Facts)
    [Organized summary of extracted facts or evidence]

    ## 🔮 NEXT MOVES
    [One final provocative thought]
    
    === CHAT LOG ===
    {conversation}
    """
    
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error generating blueprint: {e}"

def get_context(files):
    """Reads uploaded PDF or TXT files."""
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
        except Exception as e: 
            st.error(f"Error reading file: {e}")
    return text

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="Project Echo", page_icon="📡", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stFileUploader { border: 1px dashed #4b5563; border-radius: 10px; padding: 20px; }
    .stChatMessage { background-color: #1f2937; border-radius: 10px; border: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📡 Project Echo")
    
    # API Key Handling
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
        st.success("System: Online")
    else:
        api_key = st.text_input("Enter Groq API Key", type="password")
        if not api_key: st.warning("⚠️ Key Required")

    st.info("Violet: Logic (0.6) | Storm: Depth (0.9) | Lex: Discovery (0.2)")
    
    # NEW: DISCOVERY MODULE (LEX)
    st.markdown("---")
    st.header("📁 Case Discovery: LEX")
    case_mode = st.toggle("Activate LEX Mode", help="Lex will perform an audit for attorney review.")
    case_type = st.selectbox("Document Type:", ["Timeline/Log", "Exhibits", "Communication Logs", "Legal Filings"])
    
    # EXPORT BUTTON
    st.markdown("---")
    st.header("🖨️ Export")
    if api_key:
        if st.button("Generate Strategy Blueprint"):
            if "messages" in st.session_state and len(st.session_state.messages) > 1:
                with st.spinner("Compiling the Master Plan..."):
                    blueprint_text = generate_blueprint(st.session_state.messages, api_key)
                    st.download_button(
                        label="📥 Download Strategy (.txt)",
                        data=blueprint_text,
                        file_name="Project_Echo_Report.txt",
                        mime="text/plain"
                    )
                    st.success("Blueprint Ready!")
            else:
                st.warning("Chat with the agents first!")

# --- 4. MAIN INTERFACE ---
st.title("📡 Project Echo: High-Intensity Logic")
st.caption("Resilience is hardcoded. Upload files to analyze or start the sync.")

# File Ingestion
uploaded_files = st.file_uploader("Upload Knowledge Base", type=["pdf", "txt"], accept_multiple_files=True)

# THE PERSONAS
VIOLET_SYSTEM_PROMPT = """
You are VIOLET, the Architect.
Role: Technical step-by-step foundation and logic.
Personality: Resilient, clear, practical.
"""

STORM_SYSTEM_PROMPT = """
You are STORM, the Agent of Intensity.
Role: Radical Visionary thinking OUTSIDE THE BOX.
Personality: Direct, deep, abstract. Connect the dots the user doesn't see.
"""

LEX_SYSTEM_PROMPT = """
You are LEX, the Research Auditor. 
Role: Document indexing and fact extraction for legal discovery.
Task: Extract names, dates, direct quotes, and patterns. Organize chronologically.
Constraint: DO NOT PROVIDE LEGAL ADVICE. Be objective and clinical.
"""

# CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "I'm listening. Upload a file, and let's begin the discovery."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask Project Echo..."):
    if not api_key: st.stop()
    
    context_data = get_context(uploaded_files) if uploaded_files else "No specific documents provided."
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # PARALLEL AGENT EXECUTION
    def run_agent(name, prompt_text, system_prompt, temp):
        try:
            client = Groq(api_key=api_key)
            full_system = f"{system_prompt}\n\n[CONTEXT]:\n{context_data[:50000]}"
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": full_system}, {"role": "user", "content": prompt_text}],
                temperature=temp,
                stream=False
            )
            return f"**{name}:** " + completion.choices[0].message.content
        except Exception as e: return f"🚨 {name} Error: {e}"

    with st.chat_message("assistant"):
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Parallel calls for specialized agents
            future_violet = executor.submit(run_agent, "Violet", prompt, VIOLET_SYSTEM_PROMPT, 0.6)
            future_storm = executor.submit(run_agent, "Storm", prompt, STORM_SYSTEM_PROMPT, 0.9)
            
            futures = [future_violet, future_storm]
            
            # If LEX Mode is toggled on, she joins the brainstorming
            if case_mode:
                future_lex = executor.submit(run_agent, "Lex", f"[AUDIT TYPE: {case_type}] {prompt}", LEX_SYSTEM_PROMPT, 0.2)
                futures.append(future_lex)
            
            with st.spinner("Synchronizing Agents..."):
                results = [f.result() for f in futures]
        
        full_response = "\n\n---\n\n".join(results)
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
