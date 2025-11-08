import streamlit as st
import google.generativeai as genai
import os
from PyPDF2 import PdfReader

# --- Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY environment variable not set.")
    st.stop()

genai.configure(api_key=api_key)

st.set_page_config(page_title="Professional Profile", page_icon="👔")

# Hide standard Streamlit formatting (optional polish)
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("💬 Interactive Professional Profile")
st.write("Ask me anything about this candidate's experience, leadership philosophy, or technical skills.")

# --- 1. Load Your Documents ---
# Cache this so it only runs once per container start/reload, not every interaction
@st.cache_resource
def load_context():
    text_context = ""
    data_folder = "data"
    # Simple check to make sure data exists
    if not os.path.exists(data_folder):
         os.makedirs(data_folder)
         return "No documents found."

    for filename in os.listdir(data_folder):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(data_folder, filename)
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text_context += page.extract_text() + "\n"
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return text_context

FULL_CONTEXT = load_context()

# --- 2. Initialize Gemini Model ---
SYSTEM_PROMPT = f"""
You are a professional AI assistant representing a candidate for a Sr. IT Director role.
Your sole purpose is to answer questions about the candidate based ONLY on the context provided below.
If the answer is not in the context, strictly state: "I do not have that information in my current records."
Keep answers professional, concise, mission-minded, and friendly.
Do not make up facts.

CONTEXT:
{FULL_CONTEXT}
"""

# Using 1.5 Flash because it's fast, cheap (free tier available), and has a 1M token context window
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    system_instruction=SYSTEM_PROMPT
)

# --- 3. Chat UI ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat = model.start_chat(history=[])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your question here..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"An error occurred: {e}")
