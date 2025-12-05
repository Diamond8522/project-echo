import streamlit as st
from openai import OpenAI
import PyPDF2
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Grok Research Agent", page_icon="🕵️‍♂️", layout="wide")

# Custom CSS for a "Pro" look
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stFileUploader { border: 1px dashed #4b5563; border-radius: 10px; padding: 20px; }
    .stChatMessage { background-color: #1f2937; border-radius: 10px; border: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.title("🤖 Agent Controls")
    
    # API Key Input
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
        st.success("🔑 API Key Loaded")
    else:
        api_key = st.text_input("Enter Groq/xAI API Key", type="password")
        if not api_key:
            st.warning("⚠️ Key Required to Run")

    st.markdown("---")
    st.info("This agent uses **Llama 3.3 70B** (via Groq) or **Grok** logic to analyze your documents.")

# --- MAIN INTERFACE ---
st.title("📂 Document Intelligence")
st.caption("Upload PDFs or Text -> AI Analyzes Context -> You Get Answers")

# 1. FILE INGESTION
uploaded_files = st.file_uploader("Upload Knowledge Base", type=["pdf", "txt"], accept_multiple_files=True)

def get_context(files):
    text = ""
    for file in files:
        try:
            if file.type == "application/pdf":
                pdf = PyPDF2.PdfReader(file)
                for page in pdf.pages: text += page.extract_text() + "\n"
            else:
                text += io.StringIO(file.getvalue().decode("utf-8")).read()
        except: pass
    return text

# 2. SESSION MEMORY
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "I'm ready. Upload a document and ask me anything about it."}]

# 3. DISPLAY CHAT
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. CHAT LOGIC
if prompt := st.chat_input("Query your documents..."):
    
    # Validation
    if not api_key: st.stop()
    if not uploaded_files: 
        st.toast("⚠️ No documents! I'm answering from general knowledge.")
        context_data = "No documents provided."
    else:
        context_data = get_context(uploaded_files)

    # User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # AI Processing
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            
            # The "Lazy RAG" Prompt
            system_prompt = f"""
            You are an expert Research Analyst.
            Use the following CONTEXT to answer the user.
            If the answer isn't in the context, use your general knowledge but mention it.
            
            === CONTEXT START ===
            {context_data[:100000]} 
            === CONTEXT END ===
            """
            # Note: We truncate context to 100k chars to be safe on standard keys. 
            # Real Grok can handle way more.

            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            placeholder.error(f"Error: {e}")
