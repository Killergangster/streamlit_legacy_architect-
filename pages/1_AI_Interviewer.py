
import os
import streamlit as st
from dotenv import load_dotenv
import streamlit_authenticator as stauth

from utils import gemini_chat
from database import add_memory, get_memories, init_db

load_dotenv()
st.set_page_config(page_title="AI Interviewer", layout="wide")

# Paths/config same as app
BASE_DIR = os.path.dirname(__file__) or "."
ROOT = os.path.join(BASE_DIR, "..")
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
DB_PATH = os.path.join(ROOT, "data.db")

# Initialize DB in case not created
init_db(DB_PATH)

# Recreate authenticator to access session info
import yaml
with open(CONFIG_PATH, "r") as f:
    cfg = yaml.safe_load(f)
credentials = cfg.get("credentials", {})
cookie = cfg.get("cookie", {})
cookie_name = cookie.get("name", "streamlit_legacy_auth")
cookie_key = cookie.get("key", "")
cookie_expiry = cookie.get("expires_days", 30)

authenticator = stauth.Authenticate(credentials, cookie_name, cookie_key, cookie_expiry)

if not st.session_state.get("authentication_status"):
    st.warning("Please login from the main app to access the AI Interviewer.")
    st.stop()

username = st.session_state.get("username")
name = st.session_state.get("name")

st.title("AI Interviewer")
st.write(f"Hello **{name}** — this interviewer will ask questions (or accept your prompts) and save distilled memories to your account.")

with st.form("interview_form"):
    user_prompt = st.text_area("Talk to the AI interviewer (ask questions, tell a story, or provide memories):", height=180)
    tone = st.selectbox("Interviewer tone", ["curious", "professional", "empathetic", "playful"])
    submit = st.form_submit_button("Send")

if submit and user_prompt.strip():
    system_prompt = f"You are an AI interviewer that extracts concise, human-readable memories. Ask clarifying follow-ups if needed. Tone: {tone}."
    with st.spinner("Generating..."):
        response = gemini_chat(system_prompt=system_prompt, user_prompt=user_prompt)
    st.markdown("**AI Interviewer:**")
    st.write(response)
    # Save memory to DB
    try:
        mem = add_memory(DB_PATH, username=username, content=f"Q: {user_prompt}\n\nA: {response}")
        st.success("Saved memory to your account.")
    except Exception as e:
        st.error(f"Failed to save memory: {e}")

# Show recent memories
st.markdown("---")
st.subheader("Recent memories")
memories = get_memories(DB_PATH, username=username, limit=50)
if not memories:
    st.info("No memories yet. Use the form above to create and save your first memory.")
else:
    for m in memories:
        st.write(f"**{m.created_at.strftime('%Y-%m-%d %H:%M:%S')}** — {m.content}")
