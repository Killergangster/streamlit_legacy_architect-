
import os
import streamlit as st
import yaml
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
import streamlit_authenticator as stauth

from database import init_db, get_user_by_username, create_user
from utils import ensure_upload_folder

# Load environment
load_dotenv()
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

st.set_page_config(page_title="AI Legacy Architect (v0)", layout="wide")

# Initialize DB and folders
init_db(DB_PATH)
ensure_upload_folder()

# Helper: read/write config.yaml
def read_config():
    if not os.path.exists(CONFIG_PATH):
        base = {
            "credentials": {"users": {}},
            "cookie": {"name": "streamlit_legacy_auth", "key": os.getenv("STREAMLIT_AUTH_COOKIE_KEY", "changeme"), "expires_days": 30},
            "preauthorized": {}
        }
        with open(CONFIG_PATH, "w") as f:
            yaml.safe_dump(base, f)
        return base
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def write_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(cfg, f)

cfg = read_config()
credentials = cfg.get("credentials", {})
cookie = cfg.get("cookie", {})
cookie_name = cookie.get("name", "streamlit_legacy_auth")
cookie_key = cookie.get("key", os.getenv("STREAMLIT_AUTH_COOKIE_KEY", "changeme"))
cookie_expiry = cookie.get("expires_days", 30)

authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    cookie_expiry
)

st.title("AI Legacy Architect (v0)")

# --- Authentication UI ---
menu = st.sidebar.selectbox("Navigation", ["Login", "Register", "About"])

if menu == "About":
    st.markdown(
        """
        **AI Legacy Architect (v0)** — Streamlit multi-page prototype.

        Pages:
        - AI Interviewer — build personal memories via chat.
        - Digital Executor — manage assets, upload files, extract metadata with AI.

        This app uses streamlit-authenticator for session cookies and a local SQLite database for persistent user data.
        """
    )
    st.stop()

if menu == "Login":
    name, authentication_status, username = authenticator.login("Login", "main")
    if authentication_status:
        st.success(f"Welcome *{name}*")
        st.sidebar.success("Logged in")
        # Update/create user in DB if missing
        db_user = get_user_by_username(DB_PATH, username)
        if db_user is None:
            # Attempt to find email/name in config and create DB user
            users = cfg.get("credentials", {}).get("users", {})
            user_cfg = users.get(username, {})
            hashed_pw = user_cfg.get("password", None)
            display_name = user_cfg.get("name", name)
            email = user_cfg.get("email", "")
            # create user in DB (we store the bcrypt hash string exactly as in config)
            try:
                create_user(DB_PATH, username=username, name=display_name, email=email, hashed_password=hashed_pw)
            except Exception:
                pass

        # Dashboard
        st.header("Dashboard")
        st.write("Use the left sidebar (Pages) to navigate to the **AI Interviewer** or **Digital Executor**.")
        st.markdown("---")
        st.subheader("Account")
        st.write(f"**Username:** {username}")
        st.write(f"**Display name:** {name}")
        logout = st.button("Logout")
        if logout:
            authenticator.logout("main")
            st.experimental_rerun()

elif menu == "Register":
    st.header("Create an account")
    st.info("Register a new account — password will be stored (hashed) in config.yaml and a matching DB user will be created.")
    with st.form("register_form"):
        display_name = st.text_input("Full name", "")
        username = st.text_input("Username (unique)", "")
        email = st.text_input("Email", "")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Register")

    if submitted:
        if not username or not password or not display_name:
            st.error("Please fill name, username, and password.")
        elif password != password_confirm:
            st.error("Passwords do not match.")
        else:
            # Check username availability in config.yaml and DB
            users = cfg.get("credentials", {}).get("users", {})
            if username in users:
                st.error("Username already exists. Pick another.")
            else:
                # hash password with bcrypt and store in config.yaml
                hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                # Add to config structure
                if "credentials" not in cfg:
                    cfg["credentials"] = {"users": {}}
                cfg["credentials"]["users"][username] = {
                    "name": display_name,
                    "email": email or "",
                    "password": hashed
                }
                write_config(cfg)
                # Create DB user
                try:
                    create_user(DB_PATH, username=username, name=display_name, email=email, hashed_password=hashed)
                except Exception as e:
                    st.error(f"Failed to create DB user: {e}")
                st.success("Registration successful! You can now login from the Login page.")
                st.experimental_rerun()
