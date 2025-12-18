import streamlit as st
import requests
import PyPDF2
from docx import Document
import io
import re
from PIL import Image
import pytesseract
from dotenv import load_dotenv
import os

# ---------------------------
# Load API Key securely
# ---------------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ API key missing! Please set GROQ_API_KEY in environment variables.")
    st.stop()

# ---------------------------
# Tesseract OCR Config
# ---------------------------
_tesseract_env = os.getenv("TESSERACT_CMD")
_windows_default = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

if _tesseract_env and os.path.exists(_tesseract_env):
    pytesseract.pytesseract.tesseract_cmd = _tesseract_env
elif os.name == "nt" and os.path.exists(_windows_default):
    pytesseract.pytesseract.tesseract_cmd = _windows_default

# ---------------------------
# Document Processor
# ---------------------------
class DocumentProcessor:
    def process_document(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == ".txt":
                return open(filepath, "r", encoding="utf-8").read()
            elif ext == ".pdf":
                text = ""
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for p in reader.pages:
                        if p.extract_text():
                            text += p.extract_text() + "\n"
                return text
            elif ext in [".docx", ".doc"]:
                doc = Document(filepath)
                return "\n".join(p.text for p in doc.paragraphs)
            elif ext in [".png", ".jpg", ".jpeg"]:
                img = Image.open(filepath)
                return pytesseract.image_to_string(img)
            else:
                return "[Unsupported file]"
        except Exception as e:
            return f"[Error: {e}]"

doc_processor = DocumentProcessor()

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="StudyGenie - AI Chatbot",
    page_icon="🧠",
    layout="wide"
)

# ---------------------------
# Session State
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_contents" not in st.session_state:
    st.session_state.document_contents = {}

# ---------------------------
# Groq API
# ---------------------------
def get_groq_response(user_input):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    system_msg = (
        "You are StudyGenie, an AI study assistant. "
        "Explain concepts clearly, step by step, in simple language."
    )

    messages = [{"role": "system", "content": system_msg}]
    messages.extend(st.session_state.messages)
    messages.append({"role": "user", "content": user_input})

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }

    r = requests.post(url, headers=headers, json=payload)
    return r.json()["choices"][0]["message"]["content"]

# ---------------------------
# UI Header
# ---------------------------
st.markdown("<h1 style='text-align:center;'>🧠 StudyGenie</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;'>Your intelligent study companion — chat, summarize, and learn with AI ✨</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.markdown("## ⚙️ StudyGenie Settings")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages.clear()
        st.rerun()

    uploaded = st.file_uploader("📎 Upload files", type=["txt", "pdf", "docx", "png", "jpg"])
    if uploaded:
        path = f"temp/{uploaded.name}"
        os.makedirs("temp", exist_ok=True)
        with open(path, "wb") as f:
            f.write(uploaded.read())
        st.session_state.document_contents[uploaded.name] = doc_processor.process_document(path)
        st.success(f"{uploaded.name} uploaded")

# ---------------------------
# Chat Messages
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------------------
# Chat Input
# ---------------------------
user_input = st.chat_input("Ask StudyGenie anything...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        reply = get_groq_response(user_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ---------------------------
# Footer
# ---------------------------
st.markdown(
    "<p style='text-align:center;font-size:12px;color:gray;'>© 2023 StudyGenie | Powered by Groq AI</p>",
    unsafe_allow_html=True
)
