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
ROLE = os.getenv("ROLE")
if not ROLE:
    ROLE = "role"
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
if not SYSTEM_PROMPT:
    SYSTEM_PROMPT = f"""
You are a professional AI assistant representing {FORMAL_NAME} for a {ROLE} role.
Your goal is to professionally and engagingly answer questions about {CANDIDATE_NAME}'s experience based ONLY on the context provided below.

### GUIDELINES:
1.  **STRICT FACTS:** You must ONLY use the provided CONTEXT for factual information. Do not make up jobs, skills, or dates not present in the text.
2.  **POSITIVE REPRESENTATION:** You are representing the candidate. Tone should be professional, confident, and mission-minded.
3.  **AVOID REPETITION:** If asked about a general topic (like "leadership"), try to use different examples or varied details from the CONTEXT rather than repeatedly citing the same single major project. Look for smaller, relevant details in the text to provide depth.
4.  **HANDLING MISSING INFO:** If asked a factual question NOT in the context, do not just say "I do not know." Instead, say something like: "I don't have that specific detail in my current records. Could you rephrase the question, or perhaps ask about my experience with [insert a relevant major skill from context, e.g., 'Cloud Migration' or 'Team Leadership']?"
5.  **HANDLING SUBJECTIVE QUESTIONS:** If asked subjective questions (e.g., "Should I hire him?", "Is he good?"), do NOT look for those literal words in the text. Instead, respond with confidence based on the facts. Example: "While I cannot make that decision for you, {CANDIDATE_NAME}'s experience in [Skill A] and [Skill B] aligns strongly with {ROLE} responsibilities. Would you like to hear more about his leadership philosophy?"
"""

st.set_page_config(page_title=f"{FORMAL_NAME}'s Professional Profile", page_icon="👨‍💼")

# --- Custom Metatags for Social Sharing ---
# You can host your image on a site like GitHub, Imgur, or a personal website.
# Replace this with the direct URL to your image.
IMAGE_URL = os.getenv("IMAGE_URL") # e.g. "data/photo.jpg" if the photo is locally hosted with the context files
APP_URL = os.getenv("APP_URL")

meta_tags = f"""
    <meta property="og:title" content="{FORMAL_NAME}'s Professional Profile">
    <meta property="og:description" content="An interactive AI assistant trained on my professional background for the {ROLE}. Ask it anything about my experience!">
    <meta property="og:image" content="{IMAGE_URL}">
    <meta property="og:url" content="{APP_URL}"> 
    <meta name="twitter:card" content="summary_large_image">
"""
st.markdown(meta_tags, unsafe_allow_html=True)


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
st.write(f"Welcome to my interactive professional profile. This is an AI assistant trained exclusively on my resume, project portfolio, and leadership philosophy for the {ROLE}.")
st.markdown(f"""
You can ask it any question, or try one of these suggestions:
- What is {CANDIDATE_NAME}'s leadership philosophy?
- Summarize his experience with IT financial management.
- What is his strategy for AI adoption?
- Give me a detailed example of a project he has executed.
- What are the top three reasons to hire {CANDIDATE_NAME} for the {ROLE}?
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

SYSTEM_PROMPT = f"""{SYSTEM_PROMPT}

CONTEXT:
{FULL_CONTEXT}
"""

# Use the stable model name and set temperature to 0.0 for maximum factual adherence
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", # DO NOT LET THIS CHANGE TO ANYTHING LOWER THAN 2.5
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(temperature=0.3)
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
