
import os
import streamlit as st
from dotenv import load_dotenv
import streamlit_authenticator as stauth
from database import add_asset, get_assets, init_db
from utils import save_uploaded_file, gemini_explain_file, sanitize_filename

load_dotenv()
st.set_page_config(page_title="Digital Executor", layout="wide")

# Paths/config same as app
BASE_DIR = os.path.dirname(__file__) or "."
ROOT = os.path.join(BASE_DIR, "..")
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
DB_PATH = os.path.join(ROOT, "data.db")

init_db(DB_PATH)

# Authenticator recreate
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
    st.warning("Please login from the main app to access the Digital Executor.")
    st.stop()

username = st.session_state.get("username")
name = st.session_state.get("name")

st.title("Digital Executor")
st.write(f"Manage your digital assets — **{name}** ({username})")

st.sidebar.header("Actions")
action = st.sidebar.radio("Choose action", ["Upload file (AI extract)", "Add manual asset", "View assets"])

if action == "Upload file (AI extract)":
    st.header("Upload file and extract metadata with AI")
    uploaded = st.file_uploader("Choose a file to upload", accept_multiple_files=False)
    description = st.text_area("Optional description / notes about this asset", height=80)
    extract = st.checkbox("Run AI extract (Gemini) on file after upload", value=True)
    if uploaded:
        safe_name, path = save_uploaded_file(uploaded)
        st.success(f"Saved file: {safe_name}")
        ai_summary = ""
        if extract:
            with st.spinner("Analyzing file with AI..."):
                ai_summary = gemini_explain_file(path)
            st.subheader("AI Summary / Extraction")
            st.write(ai_summary)
        # Persist asset
        try:
            add_asset(DB_PATH, username=username, filename=safe_name, filepath=path, description=description or ai_summary)
            st.success("Asset recorded in your account.")
        except Exception as e:
            st.error(f"Failed to store asset: {e}")

elif action == "Add manual asset":
    st.header("Create a manual asset entry")
    fname = st.text_input("Asset name (filename or title)")
    fdesc = st.text_area("Description")
    add_btn = st.button("Add asset")
    if add_btn:
        if not fname:
            st.error("Provide an asset name.")
        else:
            safe = sanitize_filename(fname)
            # We'll not create a file on disk for manual entries; store filepath empty
            try:
                add_asset(DB_PATH, username=username, filename=safe, filepath="", description=fdesc)
                st.success("Manual asset created.")
            except Exception as e:
                st.error(f"Failed: {e}")

elif action == "View assets":
    st.header("Your assets")
    assets = get_assets(DB_PATH, username=username, limit=200)
    if not assets:
        st.info("No assets yet.")
    else:
        for a in assets:
            st.markdown("---")
            st.write(f"**{a.filename}** — uploaded {a.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if a.filepath:
                st.write(f"Path: `{a.filepath}`")
                if os.path.exists(a.filepath):
                    with open(a.filepath, "rb") as f:
                        st.download_button(label="Download", data=f, file_name=a.filename)
            st.write(a.description or "_No description_")
