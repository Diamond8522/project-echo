import streamlit as st
from groq import Groq
import PyPDF2
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Project Echo", page_icon="📡", layout="wide")

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
    st.title("📡 Project Echo")
    
    # API Key Handling
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
        st.success("Key Loaded from Secrets")
    else:
        api_key = st.text_input("Enter Groq API Key", type="password")
        if not api_key:
            st.warning("⚠️ Key Required")

    st.markdown("---")
    st.info("System: Llama 3.3 70B\nStatus: Online")

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
                for page in pdf.pages: 
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
            else:
                # Handle text files
                text += io.StringIO(file.getvalue().decode("utf-8")).read()
        except Exception as e: 
            st.error(f"Error reading file: {e}")
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
    
    if not api_key: st.stop()
    
    # Process files if they exist
    context_data = ""
    if uploaded_files: 
        context_data = get_context(uploaded_files)
    else:
        context_data = "No documents provided."

    # User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # AI Processing
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # Initialize Groq Client
            client = Groq(api_key=api_key)
            
            # The Prompt
            system_prompt = f"""
            You are an expert Research Analyst.
            Use the following CONTEXT to answer the user.
            
            === CONTEXT START ===
            {context_data[:50000]} 
            === CONTEXT END ===
            """

            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            # Stream the response
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            placeholder.error(f"Error: {e}")
