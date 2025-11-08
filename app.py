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

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME")
if not CANDIDATE_NAME:
    CANDIDATE_NAME = "this canidate"
FORMAL_NAME = os.getenv("FORMAL_NAME")
if not FORMAL_NAME:
    FORMAL_NAME = "This canidate"

st.set_page_config(page_title=f"{FORMAL_NAME}'s Professional Profile", page_icon="👨‍💼")

# Hide standard Streamlit formatting (optional polish)
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title(f"💬 {FORMAL_NAME}'s Interactive Professional Profile")
st.write("Welcome to my interactive professional profile. This is an AI assistant trained exclusively on my resume, project portfolio, and leadership philosophy for the Sr. Director of IT role.")
st.markdown(f"""
You can ask it any question, or try one of these suggestions:
- What is {CANDIDATE_NAME}'s leadership philosophy?
- Summarize his experience with IT financial management.
- What is his strategy for AI adoption?
- Give me a detailed example of a project he has executed.
- What are the top three reasons to hire {CANDIDATE_NAME} for a Sr. IT Director role?
""")

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
You are a professional AI assistant representing {FORMAL_NAME} for a Sr. IT Director role.
Your goal is to professionally and engagingly answer questions about {CANDIDATE_NAME}'s experience based ONLY on the context provided below.

### GUIDELINES:
1.  **STRICT FACTS:** You must ONLY use the provided CONTEXT for factual information. Do not make up jobs, skills, or dates not present in the text.
2.  **POSITIVE REPRESENTATION:** You are representing the candidate. Tone should be professional, confident, and mission-minded.
3.  **HANDLING MISSING INFO:** If asked a factual question NOT in the context, do not just say "I do not know." Instead, say something like: "I don't have that specific detail in my current records. Could you rephrase the question, or perhaps ask about my experience with [insert a relevant major skill from context, e.g., 'Cloud Migration' or 'Team Leadership']?"
4.  **HANDLING SUBJECTIVE QUESTIONS:** If asked subjective questions (e.g., "Should I hire him?", "Is he good?"), do NOT look for those literal words in the text. Instead, respond with confidence based on the facts. Example: "While I cannot make that decision for you, {CANDIDATE_NAME}'s experience in [Skill A] and [Skill B] aligns strongly with Sr. IT Director responsibilities. Would you like to hear more about his leadership philosophy?"

CONTEXT:
{FULL_CONTEXT}
"""

# Use the stable model name and set temperature to 0.0 for maximum factual adherence
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(temperature=0.0)
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
